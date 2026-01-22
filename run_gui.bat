@echo off
REM Check for a virtual environment and activate it
IF EXIST .\venv\Scripts\activate (
    call .\venv\Scripts\activate
    start "" pythonw gui_app.py
) ELSE (
    start "" pythonw gui_app.py
)
