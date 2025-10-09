@ECHO OFF
TITLE Discord OBS Chat Launcher

ECHO.
ECHO --- Discord OBS Chat Launcher ---
ECHO.

REM Set the name of the virtual environment directory
set VENV_DIR=.venv

REM Check if the virtual environment directory exists. If not, create it.
if not exist "%VENV_DIR%" (
    ECHO [INFO] Virtual environment not found. Creating it now...
    ECHO This will only happen once.

    REM Use 'py' launcher for better compatibility on Windows with multiple Python versions
    py -m venv %VENV_DIR%

    REM Check if the venv creation was successful
    if %errorlevel% neq 0 (
        ECHO [ERROR] Failed to create the virtual environment.
        ECHO Please make sure Python is installed and accessible via the 'py' command.
        pause
        exit /b
    )
    ECHO [SUCCESS] Virtual environment created.
    ECHO.
)

REM Activate the virtual environment. 'call' is important here!
ECHO [STEP 1] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
ECHO.

REM Install or update the required packages from requirements.txt
ECHO [STEP 2] Installing/updating required packages...
python -m pip install -U -r requirements.txt
ECHO.

REM Start the main Python server script
ECHO [STEP 3] Starting the Discord Bot and WebSocket server...
ECHO Press Ctrl+C in this window to stop the server.
ECHO.
python main.py

REM Pause at the end to see any final messages before the window closes
ECHO.
ECHO Server has been stopped.
pause