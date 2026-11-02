@echo off
rem teplo-web: backup of the PostgreSQL database. Run daily from Task Scheduler.
rem Copies are kept in BACKUP_DIR for 30 days. In Task Scheduler add the argument /auto - no pause at the end.
setlocal
cd /d "%~dp0"
set BACKUP_DIR=D:\teplo_backup
set PG_BIN=C:\Program Files\PostgreSQL\15\bin
set KEEP_DAYS=30

set DB_NAME=teplo
set DB_USER=teplo
set DB_HOST=localhost
set DB_PORT=5432
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
  if /i "%%a"=="DB_NAME" set DB_NAME=%%b
  if /i "%%a"=="DB_USER" set DB_USER=%%b
  if /i "%%a"=="DB_PASSWORD" set PGPASSWORD=%%b
  if /i "%%a"=="DB_HOST" set DB_HOST=%%b
  if /i "%%a"=="DB_PORT" set DB_PORT=%%b
)
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmm"') do set STAMP=%%d
set FILE=%BACKUP_DIR%\teplo_%STAMP%.dump

"%PG_BIN%\pg_dump.exe" -Fc -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -f "%FILE%" %DB_NAME%
if errorlevel 1 (
  echo %date% %time% ERROR backup %FILE%>> "%BACKUP_DIR%\backup.log"
  echo ERROR: backup failed.
  if /i not "%~1"=="/auto" pause
  exit /b 1
)
echo %date% %time% OK %FILE%>> "%BACKUP_DIR%\backup.log"
forfiles /p "%BACKUP_DIR%" /m teplo_*.dump /d -%KEEP_DAYS% /c "cmd /c del @path" 2>nul
echo Backup OK: %FILE%
if /i not "%~1"=="/auto" pause
exit /b 0
