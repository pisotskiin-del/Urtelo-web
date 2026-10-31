@echo off
rem teplo-web: apply a new version after unzipping it over the old folder. Data is kept.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo .venv not found. Run install.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py migrate
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py init_roles
if errorlevel 1 goto error
.venv\Scripts\python.exe teplo.pyw --shortcut
echo.
echo DONE. Close the app window if it is open and start it again.
pause
exit /b 0

:error
echo.
echo ERROR in the step above. Send the text of this window to Claude.
pause
exit /b 1
