@echo off
echo Starting EcomoveX API Server...
echo.
echo Server will run on http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.
cd /d "%~dp0"
call ..\.venv\Scripts\activate.bat
uvicorn main:app --port 8000
