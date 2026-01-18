@echo off
echo ========================================
echo   Napa Concierge - Starting Servers
echo ========================================
echo.

echo Starting Backend API...
start "Napa Backend" cmd /k "cd /d C:\Users\gageb\napa-concierge\backend && .\venv\Scripts\activate && python main.py"

echo Waiting for backend to start...
timeout /t 4 /nobreak > nul

echo Starting Frontend...
start "Napa Frontend" cmd /k "cd /d C:\Users\gageb\napa-concierge\frontend && python -m http.server 3000"

timeout /t 2 /nobreak > nul

echo Opening browser...
start http://localhost:3000/demo.html

echo.
echo ========================================
echo   Servers are running!
echo ========================================
echo.
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo   Keep the two command windows open.
echo   Close them when you're done.
echo ========================================
pause
