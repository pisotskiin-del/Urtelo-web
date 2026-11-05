@echo off
rem teplo-web: compare calculation results with the old program (D:\Teplo_dog\dbf\potreb.dbf).
rem Run the calculation in both programs for the same month first. Result: Excel file.
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
.venv\Scripts\python.exe manage.py sverka_rascheta --dir "%DBF_DIR%" --otkryt
if errorlevel 1 (
  echo ERROR. Send the text of this window to Claude.
  pause
  exit /b 1
)
pause
