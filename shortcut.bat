@echo off
rem teplo-web: create the desktop and Start menu shortcut to start the app in its own window.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run install.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe teplo.pyw --shortcut
pause
