#!/bin/bash
# WSL test script for PyInstaller build process
# Tests the bundling logic without macOS-specific features

set -e

echo "Testing PyInstaller build on WSL..."

# Clean previous builds
rm -rf build dist

# Create virtual environment
if [ ! -d "venv_wsl" ]; then
    echo "Creating WSL virtual environment..."
    python3 -m venv venv_wsl
fi

source venv_wsl/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Test basic PyInstaller analysis
echo "Testing PyInstaller analysis..."
pyinstaller --onefile --name ValleyTeacherCoverage_test --console main.py

# Check if executable was created
if [ -f "dist/ValleyTeacherCoverage_test" ]; then
    echo "✅ PyInstaller build test successful!"
    echo "Executable created: dist/ValleyTeacherCoverage_test"
    
    # Test basic import validation (without GUI)
    echo "Testing imports..."
    python -c "
import sys
sys.path.insert(0, '.')
try:
    import dearpygui.dearpygui as dpg
    import pandas as pd
    import openpyxl
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    echo "✅ WSL test complete - ready for macOS build"
else
    echo "❌ PyInstaller build failed"
    exit 1
fi
