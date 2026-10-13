@echo off
cd /d "%~dp0"
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
.venv\Scripts\python -m PyInstaller --noconfirm --clean AutoTyperPro.spec
