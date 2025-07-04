#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# exiftzsort - EXIF/metadata-based photo/video organizer
# Copyright 2025 dydo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from datetime import datetime
import argparse
from argparse import RawTextHelpFormatter
import shutil
import subprocess
import json
import filecmp
import hashlib
from PIL import Image, ExifTags
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
import os
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import tzlocal

try:
    last_used_tz = ZoneInfo(tzlocal.get_localzone_name()) if tzlocal else ZoneInfo("UTC")
except Exception:
    last_used_tz = ZoneInfo("UTC")

def update_last_used_tz(tz: ZoneInfo):
    global last_used_tz
    last_used_tz = tz

def get_last_used_tz():
    return last_used_tz

def validate_timezone(tz_str: str) -> str:
    if tz_str.lower() in ['auto', 'local']:
        return tz_str.lower()
    try:
        ZoneInfo(tz_str)
        return tz_str
    except ZoneInfoNotFoundError:
        raise argparse.ArgumentTypeError(f"Invalid timezone: '{tz_str}'. Use IANA timezone names like '{last_used_tz}'.")

LOG_LEVELS = {
    "DEBUG": 10,
    "INFO":  20,
    "WARN":  30,
    "ERROR": 40,
}
default_log_level = 'WARN'

parser = argparse.ArgumentParser(
    prog='exiftzsort',
    description='📸 exiftzsort: Organize photos/videos into date-based folders using EXIF or metadata timestamps.',
    epilog='Example: python exiftzsort.py ./input --copy --cmp-mode hash --exif-timezone {}'.format(get_last_used_tz()),
    formatter_class=RawTextHelpFormatter,
)
parser.add_argument(
    'source_dir', nargs='?', default='.',
    help='Input directory containing media files (default: current directory)',
)
parser.add_argument(
    "--output-dir", type=Path, default=Path.cwd(),
    help="Base output directory for sorted files (default: current directory)",
)
parser.add_argument(
    '--log-level', choices=LOG_LEVELS.keys(), default=default_log_level,
    help=(
        "Set minimum log level to display.\n"
        "  - DEBUG: detailed information for debugging\n"
        "  - INFO: general progress messages\n"
        "  - WARN: warnings (default)\n"
        "  - ERROR: only error messages"
    ),
)
parser.add_argument(
    '--copy', action='store_true',
    help='Copy files instead of creating symbolic links (default: symlink)',
)
parser.add_argument(
    '--cmp-mode', choices=['filecmp', 'hash'], default='filecmp',
    help='Duplicate check method: "filecmp" (fast) or "hash" (accurate)',
)
parser.add_argument(
    '--exif-timezone',
    default='local',
    type=validate_timezone,
    help=(
        "Timezone for interpreting EXIF timestamps.\n"
        '  - "auto": determine timezone from GPS coordinates if available\n'
        '  - "local": use your computer\'s local timezone (default)\n'
        '  - <IANA name>: explicitly specify timezone (e.g. "America/New_York","Asia/Tokyo")\n'
        f'Default: local ({get_last_used_tz()})'
    ),
)
parser.add_argument(
    "--enable-skip-dir",
    action="store_true",
    help="Enable skipping of specified directories",
)
parser.add_argument(
    "--skip-dirs", nargs='*',
    default=[],
    help="List of directory names to skip (used only if --enable-skip-dir is set)",
)

args = parser.parse_args()
log_level_threshold = LOG_LEVELS[args.log_level]
source_dir = Path(args.source_dir).resolve()
do_copy = args.copy
cmp_mode = args.cmp_mode
exif_tz_option_raw = args.exif_timezone
exif_tz_option = exif_tz_option_raw
if exif_tz_option_raw == 'local':
    exif_tz_option = get_last_used_tz()
skip_dirs = args.skip_dirs if args.enable_skip_dir else []

imgdirbase = args.output_dir.resolve()
err_count = 0

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif'}
VIDEO_EXTS = {'.mp4', '.mov', '.m4v', '.3gp', '.3g2', '.avi', '.mts', '.mkv', 'flv', 'm2ts', 'mpg', 'vob', 'wmv'}
RAW_EXTS   = {'.arw', '.mrw', '.cpi', '.thm', '.clpi', 'mpls', '.bdmv', '.spi', '.spd','.bup', '.ifo', '.xml', '.xmz', 'trl', '.mht'}
EXIF_DATETIME_TAGS = {'DateTimeOriginal', 'DateTime', 'CreateDate'}

def log(message: str, level: str = "INFO"):
    level = level.upper()
    msg_priority = LOG_LEVELS.get(level, 20)

    # Always display ERROR, others only if above threshold
    if msg_priority < log_level_threshold and level != "ERROR":
        return

    prefix = {
        "DEBUG": "[DEBUG]",
        "INFO":  "[INFO]",
        "WARN":  "[WARN]",
        "ERROR": "[ERROR]"
    }.get(level, f"[{level}]")

    print(f"{prefix} {message}")

def dms_to_deg_flexible(dms: tuple, ref: str) -> float:
    def to_float(x):
        return float(x[0]) / float(x[1]) if isinstance(x, tuple) else float(x)
    deg = to_float(dms[0])
    minute = to_float(dms[1])
    second = to_float(dms[2])
    result = deg + minute / 60 + second / 3600
    if ref in ['S', 'W']:
        result *= -1
    return result

def extract_latlon(tags: dict) -> tuple[float, float] | None:
    loc_str = tags.get('location') or tags.get('location-eng')
    if loc_str:
        try:
            parts = loc_str.strip('/').split('+')
            if len(parts) == 3:
                lat = float('+' + parts[1])
                lon = float('+' + parts[2])
                return lat, lon
        except Exception:
            pass
    return None

def get_datetime_from_exif(file: Path) -> datetime | None:
    try:
        with Image.open(file) as img:
            exif = img._getexif()
        if not exif:
            return None
        tag_map = {ExifTags.TAGS.get(k): v for k, v in exif.items()}
        tz = get_last_used_tz()

        if exif_tz_option == 'auto':
            gps_info = exif.get(34853)
            if gps_info:
                try:
                    lat = dms_to_deg_flexible(gps_info[2], gps_info[1])
                    lon = dms_to_deg_flexible(gps_info[4], gps_info[3])
                    tf = TimezoneFinder()
                    tz_name = tf.timezone_at(lat=lat, lng=lon)
                    if tz_name:
                        tz = ZoneInfo(tz_name)
                        update_last_used_tz(tz)
                    else:
                        tz = ZoneInfo('UTC')
                except Exception:
                    tz = ZoneInfo('UTC')

        else:
            try:
                tz = ZoneInfo(exif_tz_option)
            except Exception:
                tz = get_last_used_tz()

        for tag in EXIF_DATETIME_TAGS:
            if tag in tag_map:
                value = tag_map[tag]
                try:
                    dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    return dt.replace(tzinfo=tz)
                except ValueError:
                    continue
    except Exception:
        return None
    return None

def decimal_to_dms(decimal):
    degrees = int(abs(decimal))
    minutes_full = (abs(decimal) - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 6)
    return degrees, minutes, seconds

def convert_location_to_exif_style(location_str):
    if not location_str:
        return None

    try:
        # Example: "+28.3576-80.6501/"
        loc = location_str.strip('/')

        # Ignore leading '+', then split into latitude and longitude
        if '-' not in loc[1:]:
            return None

        idx = loc[1:].find('-') + 1
        lat_str = loc[:idx]
        lon_str = loc[idx:]

        lat = float(lat_str)
        lon = float(lon_str)

        lat_ref = 'N' if lat >= 0 else 'S'
        lon_ref = 'E' if lon >= 0 else 'W'

        lat_dms = decimal_to_dms(lat)
        lon_dms = decimal_to_dms(lon)

        return {
            'GPSLatitudeRef': lat_ref,
            'GPSLatitude': lat_dms,
            'GPSLongitudeRef': lon_ref,
            'GPSLongitude': lon_dms
        }

    except Exception as e:
        print(f"[WARN] Location parse failed: {location_str}, error: {e}")

    return None


def get_datetime_from_ffprobe(file: Path) -> datetime | None:
    cmd = [
        'ffprobe', '-hide_banner', '-v', 'quiet', '-print_format', 'json', '-show_format', str(file)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        tags = data.get('format', {}).get('tags', {})
        ct = tags.get('creation_time')
        if not ct:
            return None

        dt_utc = datetime.strptime(ct, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=ZoneInfo('UTC'))

        # Convert location to EXIF format here and use it to determine timezone
        location_str = tags.get('location') or tags.get('location-eng')
        exif_gps = convert_location_to_exif_style(location_str)
        if exif_gps:
            lat = exif_gps['GPSLatitude'][0] + exif_gps['GPSLatitude'][1] / 60 + exif_gps['GPSLatitude'][2] / 3600
            if exif_gps['GPSLatitudeRef'] == 'S':
                lat *= -1
            lon = exif_gps['GPSLongitude'][0] + exif_gps['GPSLongitude'][1] / 60 + exif_gps['GPSLongitude'][2] / 3600
            if exif_gps['GPSLongitudeRef'] == 'W':
                lon *= -1

            tz_name = TimezoneFinder().timezone_at(lat=lat, lng=lon)
            if tz_name:
                return dt_utc.astimezone(ZoneInfo(tz_name))

        return dt_utc.astimezone(ZoneInfo(tz_name if tz_name else 'UTC'))
    except Exception:
        pass
    return None

def get_md5(file: Path) -> str:
    hash_md5 = hashlib.md5()
    with file.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def files_are_same(file1: Path, file2: Path) -> bool:
    result = False
    if cmp_mode == 'filecmp':
        result = filecmp.cmp(file1, file2, shallow=True)
        log(f"Compared (filecmp): {file1} vs {file2} → {'SAME' if result else 'DIFFERENT'}", level="DEBUG")
    elif cmp_mode == 'hash':
        hash1 = get_md5(file1)
        hash2 = get_md5(file2)
        result = hash1 == hash2
        log(f"Compared (hash): {file1} [{hash1}] vs {file2} [{hash2}] → {'SAME' if result else 'DIFFERENT'}", level="DEBUG")
    return result

def process_file(file: Path):
    global err_count
    if not file.is_file() or file.stat().st_size <= 1:
        return

    ext = file.suffix.lower()

    # 📛 Check for unsupported file extensions
    if ext not in IMAGE_EXTS | VIDEO_EXTS | RAW_EXTS:
        log(f"Unsupported file type skipped: {file}", level="ERROR")
        err_count += 1
        return

    dt = None
    if ext in IMAGE_EXTS:
        dt = get_datetime_from_exif(file)
    elif ext in VIDEO_EXTS:
        dt = get_datetime_from_ffprobe(file)

    if not dt:
        try:
            dt = datetime.fromtimestamp(file.stat().st_mtime, tz=get_last_used_tz())
            log(f"Used mtime fallback for {file}: {dt}", level="INFO")
        except Exception as e:
            err_count += 1
            log(f"Failed to extract timestamp for {file}: {e}", level="ERROR")
            return

    if dt.year < 1971:
        err_count += 1
        log(f"Invalid year in timestamp (<1971) for {file}: {dt}", level="ERROR")
        return

    base_dir = imgdirbase / f"{dt.year}/{dt.year:04d}_{dt.month:02d}"
    out_dir = base_dir / 'raw' if ext in RAW_EXTS else base_dir
    out_dir.mkdir(parents=True, exist_ok=True)


    basename = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}-{dt.hour:02d}{dt.minute:02d}{dt.second:02d}"
    out_file = out_dir / (basename + ext)

    counter = 1
    while out_file.exists():
        if files_are_same(file, out_file):
            return
        out_file = out_dir / f"{basename}-{counter:02d}{ext}"
        counter += 1

    try:
        log(f"Copy or symlink: {file} → {out_file}", level="DEBUG")
        if do_copy:
            shutil.copy2(file, out_file)
            # Set timestamps
            ts = time.mktime(dt.timetuple())
            try:
                os.utime(out_file, (ts, ts), follow_symlinks=do_copy)
            except Exception as e:
                log(f"utime failed on {'link' if not do_copy else 'file'}: {out_file} → {e}", level="WARN")
        else:
            try:
                rel_path = os.path.relpath(file.resolve(), start=out_file.parent.resolve())
                out_file.symlink_to(rel_path)
            except OSError:
                log(f"symlink failed for {out_file}, falling back to copy: {e}", level="WARN")
                shutil.copy2(file, out_file)

    except Exception as e:
        err_count += 1
        log(f"File operation failed: {file} → {out_file}: {e}", level="ERROR")


for path in source_dir.rglob('*'):
    if args.enable_skip_dir and any(skip.lower() in (part.lower() for part in path.parts) for skip in skip_dirs):
        log(f"Skipped '{path}' because it matches a known directory (e.g. LINE or Facebook) where timestamps may be altered or missing.", level="WARN")
        continue
    if path.is_file():
        process_file(path)

print(f'Finished with {err_count} error(s)')
