@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 goto fail
py scripts\download_data.py
py scripts\build_database.py
pause
exit /b 0
:fail
echo Python or pip failed. Install Python 3.10+ and check internet.
pause
exit /b 1
