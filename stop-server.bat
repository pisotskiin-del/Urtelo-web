@echo off
rem teplo-web: stop the shared server - the Task Scheduler task with server.py and any
rem process listening on the server port (TEPLO_SERVER_PORT from .env, default 8000).
rem Run as administrator. The boss's copy (teplo.pyw shortcut) is not touched.
cd /d "%~dp0"
set PORT=8000
if exist .env for /f "usebackq tokens=1,* delims==" %%a in (".env") do if /i "%%a"=="TEPLO_SERVER_PORT" set PORT=%%b
powershell -NoProfile -ExecutionPolicy Bypass -Command "$port = %PORT%; $t = @(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { ($_.Actions | ForEach-Object { $_.Arguments }) -match 'server\.py' }); foreach ($x in $t) { if ($x.State -eq 'Running') { Stop-ScheduledTask -InputObject $x; Write-Host ('Task stopped: ' + $x.TaskName) } }; Start-Sleep -Seconds 2; $c = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue); foreach ($p in ($c | ForEach-Object { $_.OwningProcess } | Select-Object -Unique)) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; Write-Host ('Process stopped: ' + $p) }; Start-Sleep -Seconds 1; if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { Write-Host ('ERROR: port ' + $port + ' is still busy. Run this file as administrator.'); exit 1 } else { Write-Host ('Server stopped, port ' + $port + ' is free.') }"
pause
