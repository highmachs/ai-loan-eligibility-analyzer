@echo off
setlocal enabledelayedexpansion
title Intelligent Loan Eligibility Analyzer - Starter

echo ========================================================
echo   Starting Intelligent Loan Eligibility Analyzer...
echo ========================================================

echo [1/3] Checking Docker daemon status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker daemon is not running. Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker daemon to initialize...
    :wait_for_docker
    timeout /t 4 /nobreak >nul
    docker info >nul 2>&1
    if errorlevel 1 goto wait_for_docker
    echo Docker daemon is active!
) else (
    echo Docker daemon is running.
)

echo.
echo [2/3] Checking PostgreSQL Database container (loan_analyzer_db)...
docker compose up -d

echo Waiting for database health check...
set ATTEMPTS=0
:check_db_health
for /f "tokens=*" %%i in ('docker inspect --format="{{.State.Health.Status}}" loan_analyzer_db 2^>nul') do set DB_HEALTH=%%i
if "%DB_HEALTH%"=="healthy" (
    echo Database is healthy and ready!
    goto start_services
)
set /a ATTEMPTS+=1
if %ATTEMPTS% geq 15 (
    echo Database container started (proceeding)...
    goto start_services
)
timeout /t 2 /nobreak >nul
goto check_db_health

:start_services
echo.
echo [3/3] Launching application services...
echo Starting Backend API on port 8090...
start "Backend API (Port 8090)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8090"

echo Starting Frontend UI on port 3900...
start "Frontend UI (Port 3900)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo   All Services Initialized Successfully!
echo ========================================================
echo   Frontend Application : http://localhost:3900
echo   Backend REST API Docs: http://localhost:8090/docs
echo   pgAdmin Portal       : http://localhost:5051
echo ========================================================
echo.
pause
