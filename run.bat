@echo off
rem teplo-web: start the web application. Keep this window open while working.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run install.bat first.
  pause
  exit /b 1
)
start "" http://127.0.0.1:8000/
.venv\Scripts\python.exe manage.py runserver
pause
