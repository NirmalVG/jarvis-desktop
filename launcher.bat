@echo off
setlocal EnableDelayedExpansion
title J.A.R.V.I.S. Desktop Launcher

echo.
echo  ================================================
echo   J.A.R.V.I.S. Desktop - AI Personal Assistant
echo  ================================================
echo.

:: ── Parse flags ──────────────────────────────────────────────
set DEV_MODE=0
set NO_WAKE=0
for %%a in (%*) do (
    if "%%a"=="--dev"     set DEV_MODE=1
    if "%%a"=="--no-wake" set NO_WAKE=1
)

:: ── Check prerequisites ──────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found in PATH.
    echo          Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js not found in PATH.
    echo          Install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

:: ── Check .env file ──────────────────────────────────────────
if not exist "jarvis\.env" (
    echo  [WARN] No .env file found. Copying from .env.example...
    copy "jarvis\.env.example" "jarvis\.env" >nul 2>&1
    echo          Edit jarvis\.env and add your GROQ_API_KEY.
    echo.
)

:: ── Python backend ───────────────────────────────────────────
echo  [1/2] Starting Python backend...
cd jarvis

set PYTHON_ARGS=
if %NO_WAKE%==1 set PYTHON_ARGS=--no-wake

start "Jarvis-Backend" cmd /c "python main.py %PYTHON_ARGS% & pause"
cd ..

:: ── Wait for backend to initialise ───────────────────────────
echo  [....] Waiting for backend to boot (5s)...
timeout /t 5 /nobreak >nul

:: ── HUD Frontend ─────────────────────────────────────────────
echo  [2/2] Starting HUD frontend...
cd jarvis-hud

:: Install dependencies if node_modules missing
if not exist "node_modules" (
    echo  [....] Installing HUD dependencies...
    call npm install
)

if %DEV_MODE%==1 (
    echo  [DEV]  Starting in browser-only mode (no Electron)...
    start "Jarvis-HUD" cmd /c "npm run dev"
    timeout /t 3 /nobreak >nul
    start "" "http://localhost:5173"
) else (
    echo  [PROD] Starting Electron HUD...
    start "Jarvis-HUD" cmd /c "npm run dev"
    timeout /t 3 /nobreak >nul
    start "Jarvis-Electron" cmd /c "npx electron ."
)

cd ..

echo.
echo  ================================================
echo   All systems launched.
echo   Backend: http://localhost:6789 (WebSocket)
echo   HUD:     http://localhost:5173 (Vite dev)
echo  ================================================
echo.
echo   Flags:
echo     --dev      Browser-only mode (no Electron)
echo     --no-wake  Skip clap detection (dev testing)
echo.
echo   Press Ctrl+C in each window to stop.
echo.
