@echo off
REM Simple one-command startup for Windows
REM Runs both backend and frontend

echo.
echo ========================================
echo MAL Document Intelligence System
echo Starting backend and web UI...
echo ========================================
echo.

REM Check if venv is activated
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found.
    echo First run:  python -m venv venv
    echo Then:      venv\Scripts\activate
    echo              pip install -r requirements.txt
    echo              cd frontend ^&^& npm install
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Avoid "address already in use" (10048) if a previous server is still bound
echo Freeing ports 8000 and 3000...
powershell -NoProfile -Command 'foreach ($p in 8000,3000) { Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }'
timeout /t 2 /nobreak

REM Start backend in background
echo Starting Backend (Port 8000)...
cd backend
start "Backend - Document Intelligence" cmd /c "cd /d %~dp0backend && ..\venv\Scripts\python.exe app.py"

REM Wait for backend to bind (OCR init can take a few seconds)
timeout /t 5 /nobreak

REM Start frontend
cd ..\frontend
echo.
echo Starting Frontend (Port 3000)...
echo Opening http://localhost:3000 in browser...
echo.

call npm run dev

pause
