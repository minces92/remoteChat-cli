@echo off
echo Starting the Remote Chat CLI server...

REM Check for a virtual environment and activate it
IF EXIST .\venv\Scripts\activate (
    echo Activating virtual environment...
    call .\venv\Scripts\activate
) ELSE (
    echo Virtual environment not found. Running with global Python installation.
    echo It is recommended to use a virtual environment.
)

echo Launching Flask application...
python app.py

pause

