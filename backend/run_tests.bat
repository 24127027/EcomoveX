@echo off
echo Running EcomoveX API Tests...
echo.
echo Make sure the server is running first!
echo (Run start_server.bat in another window)
echo.
cd /d "%~dp0"
call ..\.venv\Scripts\activate.bat
python test_routers.py
pause
