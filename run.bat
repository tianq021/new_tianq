@echo off
setlocal

cd /d "%~dp0"

set "PROJECT_PY=%~dp0.venv\Scripts\python.exe"

if not exist "%PROJECT_PY%" (
    echo [ERROR] Project Python was not found:
    echo         %PROJECT_PY%
    echo.
    echo Please create the virtual environment and install dependencies first:
    echo         python -m venv .venv
    echo         .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting new_tianq with project Python...
echo URL: http://127.0.0.1:5000/
echo.

"%PROJECT_PY%" app.py

endlocal
