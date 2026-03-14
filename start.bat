@echo off
echo Starting GhostNet...

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found.
    echo Cleaning up any old locks and creating the virtual environment...
    
    :: Kill any lingering python processes that might lock venv creation
    taskkill /F /IM python.exe 2>nul
    
    :: Remove existing broken venv if it exists
    if exist "venv" rmdir /S /Q venv
    
    :: Create the virtual environment
    python -m venv venv
    
    if errorlevel 1 (
        echo [!] Failed to create virtual environment. Please check Python installation.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies to fix the 'dotenv' error 
echo Checking and installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Start the main SSH server in a new command prompt window
echo Starting SSH Honeypot Server...
start "GhostNet SSH Server" cmd /c "python main.py"

:: Start the FastAPI REST Server in a new command prompt window
echo Starting REST API Backend...
start "GhostNet API" cmd /c "uvicorn api.server:app --port 8000"

:: Start the Next.js enterprise dashboard in a new command prompt window
echo Starting Next.js Intelligence Dashboard...
start "GhostNet Dashboard" cmd /c "cd website && npm install && npm run dev"

echo.
echo GhostNet is launching!
echo The SSH server, REST API, and Dashboard are opening in separate windows.
echo You can run stop.bat to shut them all down.
timeout /t 5
