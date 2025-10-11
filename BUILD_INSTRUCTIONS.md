# Building the Valley Coverage App for Distribution

## What Was Fixed

The app was crashing when loading Excel files because of three issues:

1. **Config file path problem**: The app tried to write `config.json` to the app bundle (read-only)
2. **No writable directory**: Output files had nowhere to go in the bundled app
3. **Missing PyInstaller configuration**: No proper spec file for dependencies

### Solutions Applied

- **Writable app data directory**: Config and outputs now go to `~/Library/Application Support/ValleyCoverageApp/`
- **Proper path handling**: All file paths use the correct writable locations
- **PyInstaller spec file**: Ensures openpyxl and all dependencies are included
- **Build script**: Easy one-command rebuild

## File Locations (When Packaged)

- **Config file**: `~/Library/Application Support/ValleyCoverageApp/config.json`
- **Coverage tracker**: `~/Library/Application Support/ValleyCoverageApp/coverage_tracker.json`
- **Output files**: `~/Library/Application Support/ValleyCoverageApp/coverage_YYYY-MM-DD.txt`

## How to Build the App

### Prerequisites

Make sure you have PyInstaller installed in your environment:

```bash
cd /Users/sahajjhajharia/valleyTeacherCoverageApp
source .venv_cp/bin/activate  # or whatever your venv is called
pip install pyinstaller
```

### Build Steps

**Option 1: Use the build script (recommended)**

```bash
./build_app.sh
```

**Option 2: Manual build**

```bash
pyinstaller CoverageApp.spec
```

The app will be created at: `dist/CoverageApp.app`

### Test the Build

```bash
open dist/CoverageApp.app
```

Try loading a `Coverage_Schedule.xlsx` file from your Downloads folder. It should work now!

### Distribute to Your Friend

Create a zip file:

```bash
cd dist
zip -r CoverageApp.zip CoverageApp.app
```

Send them `CoverageApp.zip`. They can:
1. Unzip it
2. Move `CoverageApp.app` to their Applications folder
3. Run it (may need to right-click > Open the first time on macOS)

## Troubleshooting

### "App is damaged" error on macOS

This happens because the app isn't code-signed. Tell users to:
1. Right-click the app
2. Select "Open"
3. Click "Open" in the dialog

Or run this command once:
```bash
xattr -cr /path/to/CoverageApp.app
```

### Still crashing?

Check the logs. The app now writes to a proper location, so you can add debug logging:

```python
import logging
logging.basicConfig(
    filename=str(APP_DATA_DIR / "debug.log"),
    level=logging.DEBUG
)
```

### Need to reset everything?

Delete the app data:
```bash
rm -rf ~/Library/Application\ Support/ValleyCoverageApp
```

## Changes Made to main.py

1. Added `get_app_data_dir()` function to find writable directory
2. Changed `CONFIG_FILENAME` to use app data directory
3. Updated `coverage_tracker.json` path to use app data directory
4. Updated coverage output files to use app data directory

All user data is now stored in a proper, writable location that persists between app launches.
