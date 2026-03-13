@echo off
echo Stopping GhostNet Dashboard and SSH Server...

:: Kill the Streamlit dashboard
taskkill /F /FI "WINDOWTITLE eq GhostNet Dashboard" /T 2>nul

:: Kill the SSH Honeypot Server
taskkill /F /FI "WINDOWTITLE eq GhostNet SSH Server" /T 2>nul

:: Keep fallback to kill the underlying python process if the windows were closed but process detached
taskkill /F /IM python.exe 2>nul

echo GhostNet has been successfully shut down.
timeout /t 3 >nul
