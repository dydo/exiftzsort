# Changelog

All notable changes to this project will be documented here.

## [1.0.1] - 2025-07-05
### Added
- `--exif-timezone` now supports `local` (used as default)
- Improved `--help` output with wrapped descriptions and clearer formatting

### Changed
- Reformatted `argparse` definitions using multi-line syntax for readability
- Introduced early return in `convert_location_to_exif_style()` for cleaner logic
- Refactored `get_datetime_from_ffprobe()` to reduce nesting and avoid side-effects when GPS timezone detection fails
- Enhanced skip directory log messages with reasons (e.g., "LINE", "Facebook")

## [1.0.0] - 2025-06-30
### Added
- Initial release
- Organize photos/videos into date-based folders using EXIF or metadata timestamps
- Supports symbolic linking or copying
- Duplicate detection by file comparison or hashing
- Timezone interpretation from EXIF metadata (`--exif-timezone`): supports `"auto"`, `"local"`, and IANA timezone names
- Optional directory skipping with `--enable-skip-dir` and `--skip-dirs`
- User-friendly command-line help with usage examples
