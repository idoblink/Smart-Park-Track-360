"""
ParkTrack 360 — tools/test_camera.py
Real camera testing utility for Android Phone Camera (Wi-Fi IP Webcam or USB DroidCam)
and standard webcams.

Displays live camera feed, real-time FPS, and overlays the Entry & Exit lane ROIs
configured in server/config.yaml.

Usage:
  python tools/test_camera.py
  python tools/test_camera.py --source http://192.168.1.15:8080/video
  python tools/test_camera.py --source 0
"""

import sys
import time
import argparse
import yaml
from pathlib import Path
import cv2

CONFIG_PATH = Path("server/config.yaml")

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def main():
    parser = argparse.ArgumentParser(description="Test Android Phone Camera or Webcam feed with lane ROIs")
    parser.add_argument("--source", type=str, default=None,
                        help="Camera source: IP stream URL (http://<phone_ip>:8080/video) or device index (0, 1)")
    args = parser.parse_args()

    config = load_config()
    cam_cfg = config.get("camera", {})

    # Determine source: CLI argument > config.yaml > default 0
    source_val = args.source
    if source_val is None:
        source_val = cam_cfg.get("source", 0)

    # Check if source is an integer (e.g., 0, 1 for USB/DroidCam) or string (URL)
    try:
        source = int(source_val)
        is_url = False
    except (ValueError, TypeError):
        source = str(source_val).strip()
        is_url = source.startswith("http://") or source.startswith("https://") or source.startswith("rtsp://")
        # IP Webcam automatically streams video at /video
        if is_url and ":8080" in source and not (source.endswith("/video") or source.endswith("/videofeed") or source.endswith("/shot.jpg")):
            source = source.rstrip("/") + "/video"
            print(f"[AUTO-FIX] Appended '/video' endpoint: {source}")

    print("=" * 60)
    print("       ParkTrack 360 — Camera Stream Tester")
    print("=" * 60)
    print(f"Connecting to camera source: {source} ({'Wi-Fi IP Stream' if is_url else 'DirectShow / USB Device'})")
    print("Press 'q' or ESC in the preview window to exit.\n")

    if is_url:
        cap = cv2.VideoCapture(source)
    else:
        # Use CAP_DSHOW on Windows for fast DirectShow initialization
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg.get("width", 1280))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg.get("height", 720))

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera at '{source}'!")
        if is_url:
            print("\nTroubleshooting tips for Android Wi-Fi Phone Camera:")
            print("  1. Verify the 'IP Webcam' app is running on your phone and shows 'Actions... / How do I connect?'")
            print("  2. Ensure your phone and laptop are on the SAME Wi-Fi network (or laptop Mobile Hotspot).")
            print("  3. Check the exact IP displayed on your phone screen (e.g., http://192.168.X.X:8080/video).")
            print("  4. Test typing the URL into your laptop browser to see if video streams.")
        else:
            print("\nTroubleshooting tips for USB/DroidCam:")
            print("  1. Make sure DroidCam/Iriun is connected and running.")
            print("  2. Try passing --source 1 or --source 2.")
        sys.exit(1)

    print("[SUCCESS] Camera stream opened successfully!\n")

    entry_roi = cam_cfg.get("entry_roi", [440, 160, 400, 400])
    exit_roi = cam_cfg.get("exit_roi", [840, 160, 400, 400])

    prev_time = time.time()
    fps = 0.0

    window_name = "ParkTrack 360 - Camera Stream Preview (Press 'q' to quit)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARN] Dropped frame or stream paused...")
            time.sleep(0.05)
            continue

        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, now - prev_time))
        prev_time = now

        h, w = frame.shape[:2]

        # Draw Entry Lane ROI (Green box)
        if len(entry_roi) == 4:
            ex, ey, ew, eh = entry_roi
            cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            cv2.putText(frame, "ENTRY LANE ROI", (ex + 10, ey + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Draw Exit Lane ROI (Cyan box)
        if len(exit_roi) == 4:
            xx, xy, xw, xh = exit_roi
            cv2.rectangle(frame, (xx, xy), (xx + xw, xy + xh), (255, 255, 0), 2)
            cv2.putText(frame, "EXIT LANE ROI", (xx + 10, xy + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # HUD Overlay
        cv2.putText(frame, f"Source: {source}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Resolution: {w}x{h} | FPS: {fps:.1f}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "Align phone overhead so toy cars pass inside lane boxes", (20, h - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow(window_name, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' or ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\nCamera test closed.")

if __name__ == "__main__":
    main()
