@echo off
rem teplo-web: check the calculation formulas on the old program data (D:\Teplo_dog\dbf), database is not changed.
rem Run right after the calculation in the old program.
setlocal
if "%~d0"=="\\" (
  echo Run this file on the server itself ^(Remote Desktop^), not from a network folder \\Server-b\...
  pause
  exit /b 1
)
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
if not exist .venv\Scripts\python.exe (
  echo .venv not found. Run install.bat first.
  pause
  exit /b 1
)
set DBF_DIR=D:\Teplo_dog\dbf

.venv\Scripts\python.exe manage.py proverka_formul --dir "%DBF_DIR%"
if errorlevel 1 (
  echo ERROR. Send the text of this window to Claude.
  pause
  exit /b 1
)

pause
