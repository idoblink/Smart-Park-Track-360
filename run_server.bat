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

:: Find and display local IP for ESP32 and phone configuration
echo Finding your laptop's local Wi-Fi IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    for /f "tokens=1 delims= " %%b in ("%%a") do (
        echo   -- Local IP: %%b
    )
)
echo.
echo Use the IP above for your ESP32 secrets.h (e.g. server: YOUR_IP, port: 8000).
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
