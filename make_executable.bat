@echo off
setlocal enabledelayedexpansion

echo Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Creating virtual environment...
if not exist .venv (
    python -m venv .venv
    if !errorlevel! neq 0 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Installing requirements...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install pyinstaller customtkinter keyboard pyperclip

echo Creating sounds directory...
if not exist sounds mkdir sounds

echo Checking for sound files...
set missing_sounds=0
for %%s in (start.wav stop.wav finish.wav emergency.wav) do (
    if not exist "sounds\%%s" (
        echo Missing sound file: %%s
        set /a missing_sounds+=1
    )
)

if !missing_sounds! gtr 0 (
    echo.
    echo Warning: Some sound files are missing. Please add them to the sounds folder:
    echo - start.wav
    echo - stop.wav
    echo - finish.wav
    echo - emergency.wav
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

echo.
echo Creating AutoTyper Pro executable...
python -m PyInstaller --name="AutoTyperPro" ^
                     --onefile ^
                     --windowed ^
                     --add-data "sounds;sounds" ^
                     --clean ^
                     auto_typer.py

if !errorlevel! equ 0 (
    echo.
    echo Build complete! Check the dist folder for AutoTyperPro.exe
    echo.
    echo Don't forget to copy the 'sounds' folder next to your executable!
) else (
    echo.
    echo Error during build process!
    echo Please check the error messages above.
)

pause
