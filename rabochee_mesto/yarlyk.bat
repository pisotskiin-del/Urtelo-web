@echo off
rem Creates the desktop shortcut "Teplosnabzhenie" for a workstation. Python is not needed.
rem Server address: change ADRES below if the server or port is different.
set ADRES=http://Server-b:8020/
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0yarlyk.ps1" -Adres %ADRES%
pause
