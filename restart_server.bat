@echo off
echo Restarting the Remote Chat CLI server...

REM 포트 5000을 사용하는 프로세스 종료
echo Checking for processes on port 5000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    echo Killing process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

REM 잠시 대기
timeout /t 2 /nobreak >nul

REM Check for a virtual environment and activate it
IF EXIST .\venv\Scripts\activate (
    echo Activating virtual environment...
    call .\venv\Scripts\activate
) ELSE (
    echo Virtual environment not found. Running with global Python installation.
    echo It is recommended to use a virtual environment.
)

echo Launching Flask application...
start "Remote Chat CLI Server" python app.py

echo Server restart initiated.
pause

