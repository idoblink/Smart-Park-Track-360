import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[ParkTrack 360] Starting server on {host}:{port} (Python {sys.version.split()[0]})...")
    uvicorn.run("server.app:app", host=host, port=port, log_level="info")
