#!/usr/bin/env bash
echo "======================================================="
echo "         ParkTrack 360 - FastAPI Server Runner         "
echo "======================================================="
echo ""
echo "Starting server on http://localhost:8000 ..."
echo "Press Ctrl+C to stop the server."
echo ""
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
