@echo off
title ParkTrack 360 - Server
cd /d "%~dp0"

echo =======================================================
echo          ParkTrack 360 - Smart Parking Server         
echo =======================================================
echo.

:: Detect Python executable
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PY_EXE=python
) else (
    set PY_EXE="C:\Users\Hades\AppData\Local\Programs\Python\Python311\python.exe"
)

echo Hardware Connection:
echo   - USB Camera 1: Entry Lane (DirectShow Index 1)
echo   - USB Camera 2: Exit Lane  (DirectShow Index 2)
echo   - USB Serial:   ESP32 Controller (Auto-detected / COM3)
echo.
echo =======================================================
echo Starting server on http://localhost:8000 ...
echo Opening web dashboard in your browser...
echo Press Ctrl+C in this terminal window to stop the server.
echo =======================================================
echo.

:: Launch browser in background after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Start Uvicorn FastAPI Server
%PY_EXE% -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

pause
