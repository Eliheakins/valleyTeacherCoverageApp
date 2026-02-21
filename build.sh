#!/bin/bash

# Local build script for Valley Teacher Coverage App
# This script creates a macOS app bundle and DMG for local testing

set -e

echo "Building Valley Teacher Coverage App..."

# Clean previous builds
rm -rf build dist *.dmg dmg_contents

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Build the app
echo "Building app with PyInstaller..."
pyinstaller build.spec --clean

# Create DMG
echo "Creating DMG..."
mkdir -p dmg_contents
cp -R "dist/ValleyTeacherCoverage.app" dmg_contents/
ln -s /Applications dmg_contents/Applications

hdiutil create -volname "Valley Teacher Coverage" -srcfolder dmg_contents -ov -format UDZO "ValleyTeacherCoverage.dmg"

# Clean up
rm -rf dmg_contents

echo "Build complete!"
echo "App bundle: dist/ValleyTeacherCoverage.app"
echo "DMG file: ValleyTeacherCoverage.dmg"

# Optional: Open the DMG
read -p "Open the DMG? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open ValleyTeacherCoverage.dmg
fi
