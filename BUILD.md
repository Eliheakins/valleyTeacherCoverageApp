# Build Instructions

## GitHub Actions (Automatic)

The GitHub Actions workflow will automatically build the macOS app when:
- Code is pushed to `main` or `develop` branches
- A new tag is created (e.g., `v1.0.0`)
- Manual workflow dispatch

### Workflow Features
- **Builds on macOS** using the latest runner
- **Caches dependencies** for faster builds
- **Creates both app bundle and DMG**
- **Automatic releases** when tags are pushed
- **Artifacts available** for 30 days

### Accessing Builds
1. Go to the **Actions** tab in your GitHub repository
2. Select the **Build macOS App** workflow
3. Download artifacts from the workflow run
4. For tagged releases, check the **Releases** page

## Local Build (macOS)

### Prerequisites
- macOS 10.15 or later
- Python 3.11 or later
- Xcode Command Line Tools (for `hdiutil`)

### Quick Build
```bash
# Make the build script executable (on macOS/Linux)
chmod +x build.sh

# Run the build
./build.sh
```

### Manual Build
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Build the app
pyinstaller build.spec --clean

# Create DMG manually
mkdir -p dmg_contents
cp -R "dist/ValleyTeacherCoverage.app" dmg_contents/
ln -s /Applications dmg_contents/Applications
hdiutil create -volname "Valley Teacher Coverage" -srcfolder dmg_contents -ov -format UDZO "ValleyTeacherCoverage.dmg"
```

## Output Files

### App Bundle
- **Location**: `dist/ValleyTeacherCoverage.app`
- **Type**: macOS application bundle
- **Usage**: Double-click to run, or copy to `/Applications`

### DMG Installer
- **Location**: `ValleyTeacherCoverage.dmg`
- **Type**: Disk image installer
- **Usage**: Mount and drag app to Applications folder

## Build Configuration

### PyInstaller Spec File (`build.spec`)
- **Console**: Disabled (GUI app)
- **Bundle**: Creates `.app` package
- **Icon**: None (add icon file path if available)
- **Dependencies**: Auto-collected from `requirements.txt`

### Dependencies (`requirements.txt`)
- `dearpygui>=1.11.0` - GUI framework
- `pandas>=2.0.0` - Excel/CSV processing
- `openpyxl>=3.1.0` - Excel file support

## Troubleshooting

### Common Issues
1. **"Command not found: hdiutil"** - Install Xcode Command Line Tools
2. **"PyInstaller not found"** - Install with `pip install pyinstaller`
3. **"Permission denied"** - Use `chmod +x build.sh` on macOS/Linux

### Windows Build
The current configuration is macOS-specific. For Windows builds, you would need:
- Windows runner in GitHub Actions
- Different PyInstaller spec (no .app bundle)
- NSIS or similar for installer creation

### Code Signing
For distribution outside the App Store, you may want to:
1. Get a Developer ID certificate from Apple
2. Add codesigning to the build process
3. Notarize the app with Apple

## Version Management

### Semantic Versioning
Use git tags for releases:
```bash
git tag v1.0.0
git push origin v1.0.0
```

### Automatic Releases
When you push a tag starting with `v`, GitHub Actions will:
1. Build the app
2. Create a GitHub Release
3. Attach the DMG and app bundle as release assets
