@echo off
rem teplo-web: run the program as a server for several computers (see README).
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo .venv not found. Run install.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe server.py
pause
