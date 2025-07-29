#!/bin/bash

echo "Creating Auto Typer Pro executable for macOS..."

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it from python.org"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Create sounds directory if it doesn't exist
if [ ! -d "sounds" ]; then
    echo "Creating sounds directory..."
    mkdir sounds
fi

# Check for sound files
missing_sounds=0
for sound in start.wav stop.wav finish.wav emergency.wav; do
    if [ ! -f "sounds/$sound" ]; then
        echo "Missing sound file: $sound"
        ((missing_sounds++))
    fi
done

if [ $missing_sounds -gt 0 ]; then
    echo ""
    echo "Warning: Some sound files are missing. Please add them to the sounds folder:"
    echo "- start.wav"
    echo "- stop.wav"
    echo "- finish.wav"
    echo "- emergency.wav"
    echo ""
    read -p "Press Enter to continue anyway..."
fi

# Create the executable
echo ""
echo "Creating executable..."
python3 -m PyInstaller \
    --name="AutoTyperPro" \
    --onefile \
    --windowed \
    --add-data "sounds:sounds" \
    --clean \
    auto_typer.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Build complete! Check the dist folder for AutoTyperPro.app"
    echo ""
    echo "Don't forget to:"
    echo "1. Copy the 'sounds' folder next to your executable"
    echo "2. Grant accessibility permissions to the app in System Preferences"
else
    echo ""
    echo "Error during build process!"
    echo "Please check the error messages above."
fi

# Deactivate virtual environment
deactivate
