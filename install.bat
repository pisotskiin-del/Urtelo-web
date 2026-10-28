@echo off
rem teplo-web: installation and first data load. Run once.
cd /d "%~dp0"
echo Folder: %CD%
if not exist manage.py (
  echo manage.py not found here. Unzip the whole archive first, then run install.bat from the unzipped folder.
  pause
  exit /b 1
)

where python
if errorlevel 1 (
  echo Python not found. Install Python 3.12 from python.org and tick "Add python.exe to PATH".
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
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py migrate
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py init_roles
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py dbf_import --dir D:\teplo_dog\dbf
if errorlevel 1 goto error

echo.
set /p ADMIN_PASS=Enter a password for user admin: 
.venv\Scripts\python.exe manage.py add_user admin --role admin --password "%ADMIN_PASS%" --name "Admin"
if errorlevel 1 goto error

.venv\Scripts\python.exe teplo.pyw --shortcut

echo.
echo DONE. Start the app with the desktop shortcut (or run.bat).
pause
exit /b 0

:error
echo.
echo ERROR in the step above. Send the text of this window to Claude.
pause
exit /b 1
