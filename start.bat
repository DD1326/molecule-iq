@echo off
title MoleculeIQ Platform
echo ==============================================================
echo   MoleculeIQ - Intelligent Drug Repurposing Platform 
echo   Team: AI Avengers - SVCE Blueprints 2026
echo ==============================================================
echo.
echo Installing/Verifying Python dependencies...
python -m pip install -r requirements.txt

echo.
echo Starting the Flask backend server...
echo Please leave this window open. 
echo Press Ctrl+C to stop the server later.
echo.

python app.py

pause
