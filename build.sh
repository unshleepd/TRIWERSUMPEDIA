#!/bin/bash
echo "Packaging the Triwersum Roguelike game..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller not found. Please install it first:"
    echo "pip install pyinstaller"
    exit
fi

# Run PyInstaller
pyinstaller --onefile --windowed --name TriwersumRoguelike src/main.py

echo "Build complete! The executable can be found in the 'dist' directory."
