#!/bin/bash

# Build script for Valley Coverage App
# This script builds the macOS .app bundle using PyInstaller

echo "Building Valley Coverage App..."
echo "=============================="

# Activate virtual environment
if [ -d ".venv_cp" ]; then
    echo "Activating virtual environment (.venv_cp)..."
    source .venv_cp/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
else
    echo "Warning: No virtual environment found. Using system Python."
fi

# Check if PyInstaller is installed, if not, install it
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build with PyInstaller using the spec file
echo "Running PyInstaller..."
pyinstaller CoverageApp.spec

# Check if build was successful
if [ -d "dist/CoverageApp.app" ]; then
    echo ""
    echo "✓ Build successful!"
    echo "  App location: dist/CoverageApp.app"
    echo ""
    echo "To test the app, run:"
    echo "  open dist/CoverageApp.app"
    echo ""
    echo "To distribute, compress the .app:"
    echo "  cd dist && zip -r CoverageApp.zip CoverageApp.app"
else
    echo ""
    echo "✗ Build failed. Check the output above for errors."
    exit 1
fi
