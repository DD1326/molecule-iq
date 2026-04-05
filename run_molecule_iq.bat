@echo off
echo MoleculeIQ - Initializing Dual-Portal Environment...
echo.

echo [1/2] Launching Student Portal (Port 5000)...
start "MoleculeIQ Student Portal" cmd /k "python app.py"

echo [2/2] Launching Admin Management Portal (Port 5001)...
start "MoleculeIQ Admin Portal" cmd /k "python admin_portal.py"

echo.
echo Done! Both portals are now starting in separate windows.
echo - Student View: http://127.0.0.1:5000
echo - Admin Control: http://127.0.0.1:5001
echo.
pause
