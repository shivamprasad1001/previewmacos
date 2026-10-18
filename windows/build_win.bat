@echo off
REM ==============================================================================
REM Windows Build Script for Preview (macOS Edition)
REM Developer: Shivam Prasad
REM Powered by: TriviLabs.in
REM ==============================================================================

echo [1/3] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

echo [2/3] Freezing executable with PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name="Preview" ^
    --icon="preview/assets/icon.ico" ^
    --add-data "preview/assets;preview/assets" ^
    --hidden-import fitz ^
    --hidden-import pymupdf ^
    main.py

echo [3/3] To build the setup installer, compile windows/setup.iss using Inno Setup Compiler (ISCC):
echo "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" windows\setup.iss

echo Build complete! Frozen app is in dist\Preview\
pause
