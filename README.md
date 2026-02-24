# Valley Teacher Coverage Application

A desktop application for calculating daily teacher coverage assignments based on pre-formatted schedule files. Optimizes assignments by prioritizing the least-covered staff while respecting duty constraints and co-teaching relationships.

## Features

- **Smart Assignment Algorithm**: Assigns coverage to teachers with the lowest coverage count first
- **Co-Teaching Support**: Automatically handles CT (co-taught) periods based on co-teacher availability
- **Day-Specific Availability**: Respects Even Day/Odd Day duty assignments
- **Split Period Handling**: Correctly assigns coverage for split periods (e.g., 5/6) to single teachers
- **Multiple File Formats**: Supports both Excel (.xlsx) and CSV (.csv) schedule files
- **Coverage Tracking**: Maintains JSON-based coverage history across sessions
- **Clipboard Integration**: One-click copy of results for easy sharing
- **Cross-Platform**: Runs on Windows, macOS, and Linux

---

## For End Users

### Installation

#### macOS (via GitHub Actions Build)
1. Download `ValleyTeacherCoverage.dmg` from the [Releases](../../releases) page
2. Open the DMG and drag `ValleyTeacherCoverage.app` to your Applications folder
3. Right-click the app and select "Open" (first time only, for Gatekeeper)

#### Windows/Linux (From Source)
1. Download the source code from [Releases](../../releases)
2. Install Python 3.8 or higher
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`

---

## Usage Guide

### First Launch: Schedule File Selection

On first run, the app prompts you to select your schedule file:

1. **Launch** the application
2. **Browse** for your schedule file (Excel .xlsx or CSV .csv)
3. **Select** the file and confirm
4. The file path is saved to `config.json` in your app data directory

To change the schedule file later, click "Change Schedule File" in the main window.

### Daily Coverage Calculation

1. **Select Teachers Out**: Check boxes for all absent teachers
2. **Verify Date**: Confirm or edit the date (YYYY-MM-DD format)
3. **Select Day Type**: Check "Even Day" for even-day schedules, leave unchecked for odd days
4. **Submit**: Click "Submit" to calculate coverage

### Results

The results window displays coverage assignments by teacher, with periods marked `(CT)` for co-taught coverage.

**Output Files** (saved to app data directory):
- `coverage_YYYY-MM-DD.txt` - Human-readable coverage report
- `coverage_tracker.json` - Coverage statistics for tracking

---

## Schedule File Format

The app requires a schedule file in Excel (.xlsx) or CSV (.csv) format.

**Required Columns:**
- `Name` - Teacher names in "Last, First" format
- `Need Coverage` - Periods needing coverage (e.g., "1,4,11" or "5/6")
- `1st` through `11th` - Period schedule data with CT markers
- `Duty 1st` through `Duty 11th` - Duty assignments for availability

**See [EXCEL_SETUP_GUIDE.txt](EXCEL_SETUP_GUIDE.txt) for complete formatting details.**

The app now automatically handles common formatting issues (spaces, extra whitespace, etc.) and auto-detects co-taught periods.

---

## For Developers

### Setup

```bash
git clone https://github.com/Eliheakins/valleyTeacherCoverageApp.git
cd valleyTeacherCoverageApp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Testing

```bash
pytest                    # Run all tests
pytest --cov=main        # With coverage
```

### Building

See [BUILD.md](BUILD.md) for detailed build instructions.

---

## License

[Add your license here]
