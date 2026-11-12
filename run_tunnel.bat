@echo off
echo ===================================================
echo   ParkTrack 360 - Secure Cloudflare Public Tunnel
echo ===================================================
echo.
echo Starting secure HTTPS tunnel to http://localhost:8000 ...
echo Look for the public URL ending in '.trycloudflare.com' below!
echo.
tools\cloudflared.exe tunnel --url http://localhost:8000
pause

