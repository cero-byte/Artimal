@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not defined ARTIMAL_PORT set ARTIMAL_PORT=8920
if not defined ARTIMAL_BIND set ARTIMAL_BIND=127.0.0.1
set URL=http://127.0.0.1:%ARTIMAL_PORT%/

echo Starting Artimal at %URL%
echo Keep this window open. Press Ctrl+C to stop.
start "" "%URL%"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py
  goto end
)
where python >nul 2>nul
if %errorlevel%==0 (
  python server.py
  goto end
)
echo Python 3 was not found. Install it from https://www.python.org/downloads/windows/
pause
:end
endlocal
