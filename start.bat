@echo off
echo Starting Loan Eligibility Analyzer...

echo [1/3] Starting database...
echo Checking if Docker is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to spin up ^(this may take a moment^)...
    :wait_for_docker
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 goto wait_for_docker
    echo Docker started successfully!
)

docker compose up -d
timeout /t 3 /nobreak >nul

echo [2/3] Starting backend on port 8090...
start "Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8090"

echo [3/3] Starting frontend on port 3900...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo All services started.
echo   Backend : http://localhost:8090
echo   Frontend: http://localhost:3900
echo   pgAdmin : http://localhost:5051
echo.
pause
