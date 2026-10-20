@echo off
REM Windows (cmd / PowerShell)
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Done. Open .env and paste your GEMINI_API_KEY, then run:
echo   venv\Scripts\activate ^&^& python test_connection.py
