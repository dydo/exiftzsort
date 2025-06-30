# 📸 exiftzsort

**exiftzsort** is a CLI tool that organizes image and video files into date-based directories using EXIF or metadata timestamps. It supports time zone adjustments (manual or GPS auto-detection), and can organize files via copy or symbolic links. Logging verbosity can be adjusted using the `--log-level` option.

---

## ✨ Features

- Extracts datetime from EXIF or FFprobe metadata
- Automatically detects timezone from GPS (using `--exif-timezone auto`)
- Organizes files into `YYYY/YYYY_MM`-style folders
- Avoids duplicate files by comparing content (method selectable)
- Supports copy or symbolic link output
- Adjustable logging level (`DEBUG`, `INFO`, `WARN`, `ERROR`)

---

## 🛠 Options

| Option            | Description                                                                         |
| ----------------- | ----------------------------------------------------------------------------------- |
| `source_dir`      | Input directory (defaults to current directory)                                     |
| `--output-dir`    | Base output directory (default: current working directory)                          |
| `--copy`          | Copy files instead of creating symbolic links                                       |
| `--cmp-mode`      | Duplicate comparison method: `filecmp` (fast) or `hash` (accurate)                  |
| `--exif-timezone` | Timezone for EXIF timestamps (`auto` to detect from GPS)                            |
| `--log-level`     | Minimum log level to display: `DEBUG` / `INFO` / `WARN` / `ERROR` (default: `WARN`) |
| `-h`, `--help`    | Show help                                                                           |

---

## 🧪 Log Level Examples

```bash
# Warnings and errors only (default)
python exiftzsort.py ./media

# Show INFO, WARN, and ERROR
python exiftzsort.py ./media --log-level INFO

# Show all logs including DEBUG
python exiftzsort.py ./media --log-level DEBUG

# Show only ERROR (quiet mode)
python exiftzsort.py ./media --log-level ERROR
```

---

## 🔧 Installation

### Dependencies

```bash
pip install pillow timezonefinder
```

*Note: **`ffprobe`** (from **`ffmpeg`**) is required for video timestamp extraction.*

---

## 🚀 Usage Examples

```bash
# Default (process current directory)
python exiftzsort.py

# Copy mode + specific timezone
python exiftzsort.py ./import --copy --exif-timezone Asia/Tokyo

# Hash comparison + debug log
python exiftzsort.py ./media --cmp-mode hash --log-level DEBUG

# Specify output base directory
python exiftzsort.py ./media --output-dir ./sorted_output
```

---

## 📂 Example Output Structure

```
Pict_works/
mq New/
    tq 2023/
    x   mq 2023_07/
    x       tq 20230725-102015.jpg
    x       tq 20230725-102016-01.jpg
    x       mq raw/
    x           tq 20230725-102017.dng
    x           mq 20230725-102018-01.cr2
```

---

## 📍 License

Apache License 2.0\
Copyright (c) 2025 dydo

---

## 😋 Author

Created by **dydo**\
Contributions welcome!

---

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind, express or implied.
The author assumes no responsibility for any damage, data loss, or consequences resulting from the use of this tool.
**Please ensure you have a complete backup of your files before using this tool. Use at your own risk.**

