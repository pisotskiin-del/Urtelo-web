@echo off
rem teplo-web: update meter readings, heating days, recalculation, GVS losses and consumption of the cards and the calculation input data
rem from the old program (DBF in D:\Teplo_dog\dbf). For parallel work while the new program is tested.
rem   obnovit-iz-staroj.bat            - update
rem   obnovit-iz-staroj.bat /proverka  - only show what would change
rem   obnovit-iz-staroj.bat /auto      - no pause at the end (Task Scheduler)
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
set ARGS=
if /i "%~1"=="/proverka" set ARGS=--proverka
.venv\Scripts\python.exe manage.py obnovit_iz_staroj --dir "%DBF_DIR%" %ARGS%
set RC=%errorlevel%
if not "%RC%"=="0" echo ERROR: data not updated. Send the text of this window to Claude.
if /i not "%~1"=="/auto" pause
exit /b %RC%
