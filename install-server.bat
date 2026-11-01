@echo off
rem teplo-web on Server-b: install with PostgreSQL and move data from the old db.sqlite3. Run once.
cd /d "%~dp0"
echo Folder: %CD%
if not exist manage.py (
  echo manage.py not found here. Unzip the whole archive first.
  pause
  exit /b 1
)
if not exist .env (
  echo File .env not found in this folder. Create it first (see the instruction).
  pause
  exit /b 1
)
findstr /b /c:"DB_ENGINE=postgresql" .env >nul
if errorlevel 1 (
  echo .env has no line DB_ENGINE=postgresql. Fix .env first.
  pause
  exit /b 1
)
where python
if errorlevel 1 (
  echo Python not found. Install Python 3.13 from python.org for all users with "Add python.exe to PATH".
  pause
  exit /b 1
)
python --version
if not exist .venv\Scripts\python.exe (
  echo Creating .venv ...
  python -m venv .venv
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements-server.txt
if errorlevel 1 goto error

echo.
set SRC=%~dp0db.sqlite3
set /p SRC=Path to the old db.sqlite3 [%SRC%]: 
.venv\Scripts\python.exe manage.py perenos_v_postgres --iz "%SRC%"
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py collectstatic --noinput
if errorlevel 1 goto error

echo.
echo DONE. Start server.bat and open http://localhost:8020/ (port from TEPLO_SERVER_PORT).
pause
exit /b 0

:error
echo.
echo ERROR in the step above. Send the text of this window to Claude.
pause
exit /b 1
