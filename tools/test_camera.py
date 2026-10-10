"""
ParkTrack 360 — tools/test_camera.py
Real camera testing utility supporting:
  1. Dual USB Webcams (one dedicated for Entry lane, one for Exit lane)
  2. Single Overhead Camera / Phone Wi-Fi Stream with ROI split
  3. Automatic USB camera device scanning (--list)

Usage Examples:
  python tools/test_camera.py --list                 # Scan & list all connected USB cameras
  python tools/test_camera.py --dual                 # Live side-by-side preview of Entry + Exit webcams
  python tools/test_camera.py --lane entry           # Test Entry lane webcam only
  python tools/test_camera.py --lane exit            # Test Exit lane webcam only
  python tools/test_camera.py --source 0             # Test specific camera index
  python tools/test_camera.py --source http://...    # Test Android phone Wi-Fi stream
"""

import sys
import time
import argparse
import yaml
from pathlib import Path
import cv2
import numpy as np

CONFIG_PATH = Path("server/config.yaml")

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def parse_source(src_val):
    """Parses a source value into an integer index or clean URL string."""
    try:
        return int(src_val), False
    except (ValueError, TypeError):
        s = str(src_val).strip()
        is_url = s.startswith("http://") or s.startswith("https://") or s.startswith("rtsp://")
        if is_url and ":8080" in s and not (s.endswith("/video") or s.endswith("/videofeed") or s.endswith("/shot.jpg")):
            s = s.rstrip("/") + "/video"
        return s, is_url

def open_capture(source, is_url, width=1280, height=720):
    """Opens a VideoCapture with DirectShow (on Windows) or standard backend."""
    if is_url:
        cap = cv2.VideoCapture(source)
    else:
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        # Request MJPG to conserve USB bus bandwidth when multiple cameras are connected
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    return cap

def list_connected_cameras(max_devices=6):
    """Scans and lists connected USB video devices on Windows DirectShow."""
    print("=" * 65)
    print("       ParkTrack 360 — USB Camera Device Scanner")
    print("=" * 65)
    print("Probing DirectShow video devices (Indices 0 to 5)...")
    found = []
    for i in range(max_devices):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                found.append((i, w, h))
                print(f"  -> Camera Index [{i}]: AVAILABLE  (Frame: {w}x{h})")
            else:
                found.append((i, 0, 0))
                print(f"  -> Camera Index [{i}]: DETECTED  (Device opened)")
            cap.release()
        else:
            pass

    print("-" * 65)
    if found:
        print(f"Found {len(found)} active camera device(s).")
        if len(found) >= 2:
            print("\nSetup recommendation for 2 USB Webcams:")
            print(f"  Entry Lane Webcam: Index {found[0][0]}")
            print(f"  Exit Lane Webcam:  Index {found[1][0]}")
            print("\nConfigure server/config.yaml:")
            print("  camera:")
            print("    mode: \"dual\"")
            print(f"    entry:\n      source: {found[0][0]}")
            print(f"    exit:\n      source: {found[1][0]}")
        elif len(found) == 1:
            print(f"1 camera detected at Index {found[0][0]}. Plug in your second USB webcam to test dual mode.")
    else:
        print("No USB cameras detected. Verify USB cables are connected firmly.")
    print("=" * 65)

def run_single_camera(source, is_url, title="ParkTrack 360 - Camera Preview", cam_cfg=None):
    """Runs a single camera preview window."""
    if cam_cfg is None:
        cam_cfg = {}
    width = cam_cfg.get("width", 1280)
    height = cam_cfg.get("height", 720)
    entry_roi = cam_cfg.get("entry_roi", [440, 160, 400, 400])
    exit_roi = cam_cfg.get("exit_roi", [840, 160, 400, 400])

    print(f"Opening camera: {source} ({'Network Stream' if is_url else 'USB / DirectShow'})...")
    cap = open_capture(source, is_url, width, height)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera at '{source}'!")
        return False

    print("[SUCCESS] Camera stream opened! Press 'q' or ESC to exit.")
    window_name = f"{title} (Press 'q' to quit)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    fps = 0.0
    prev_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.02)
            continue

        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(1e-5, now - prev_time))
        prev_time = now

        h, w = frame.shape[:2]

        # Draw ROIs if configured (used for single camera setup)
        if len(entry_roi) == 4 and "Single" in title:
            ex, ey, ew, eh = entry_roi
            cv2.rectangle(frame, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            cv2.putText(frame, "ENTRY LANE ROI", (ex + 10, ey + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if len(exit_roi) == 4 and "Single" in title:
            xx, xy, xw, xh = exit_roi
            cv2.rectangle(frame, (xx, xy), (xx + xw, xy + xh), (255, 255, 0), 2)
            cv2.putText(frame, "EXIT LANE ROI", (xx + 10, xy + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        # HUD
        cv2.putText(frame, f"{title} | Source: {source}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Resolution: {w}x{h} | FPS: {fps:.1f}", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    return True

def run_dual_cameras(entry_src, exit_src, cam_cfg):
    """Runs Entry and Exit USB webcams simultaneously with split-screen preview."""
    e_source, e_is_url = parse_source(entry_src)
    x_source, x_is_url = parse_source(exit_src)

    e_cfg = cam_cfg.get("entry", {})
    x_cfg = cam_cfg.get("exit", {})

    print("=" * 65)
    print("       ParkTrack 360 — Dual USB Webcam Monitor")
    print("=" * 65)
    print(f"  Entry Lane Camera: Source {e_source} ({'DirectShow Index' if not e_is_url else 'URL'})")
    print(f"  Exit Lane Camera:  Source {x_source} ({'DirectShow Index' if not x_is_url else 'URL'})")
    print("Press 'q' or ESC in the preview window to exit.\n")

    cap_entry = open_capture(e_source, e_is_url, e_cfg.get("width", 1280), e_cfg.get("height", 720))
    cap_exit = open_capture(x_source, x_is_url, x_cfg.get("width", 1280), x_cfg.get("height", 720))

    e_ok = cap_entry.isOpened()
    x_ok = cap_exit.isOpened()

    if not e_ok or not x_ok:
        if not e_ok:
            print(f"[ERROR] Could not open ENTRY camera at source '{e_source}'!")
        if not x_ok:
            print(f"[ERROR] Could not open EXIT camera at source '{x_source}'!")
        print("\nTip: Run 'python tools/test_camera.py --list' to find valid camera device indices.")
        if cap_entry.isOpened():
            cap_entry.release()
        if cap_exit.isOpened():
            cap_exit.release()
        return False

    print("[SUCCESS] Both Entry and Exit cameras opened successfully!")
    window_name = "ParkTrack 360 — Dual Camera Monitor (Entry [Left] | Exit [Right])"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    fps_e = 0.0
    fps_x = 0.0
    t_prev = time.time()

    try:
        while True:
            ret_e, frame_e = cap_entry.read()
            ret_x, frame_x = cap_exit.read()

            now = time.time()
            dt = max(1e-5, now - t_prev)
            t_prev = now

            if ret_e and frame_e is not None:
                fps_e = 0.9 * fps_e + 0.1 * (1.0 / dt)
                he, we = frame_e.shape[:2]
                # Entry Lane HUD (Green styling)
                cv2.rectangle(frame_e, (0, 0), (we, 50), (30, 80, 30), -1)
                cv2.putText(frame_e, f"[ENTRY LANE] Cam {e_source} | {we}x{he} | {fps_e:.1f} FPS", (15, 34),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 120), 2)
                cv2.rectangle(frame_e, (0, 0), (we - 1, he - 1), (0, 255, 120), 3)
            else:
                frame_e = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame_e, "ENTRY CAMERA WAITING", (50, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if ret_x and frame_x is not None:
                fps_x = 0.9 * fps_x + 0.1 * (1.0 / dt)
                hx, wx = frame_x.shape[:2]
                # Exit Lane HUD (Cyan styling)
                cv2.rectangle(frame_x, (0, 0), (wx, 50), (80, 60, 20), -1)
                cv2.putText(frame_x, f"[EXIT LANE] Cam {x_source} | {wx}x{hx} | {fps_x:.1f} FPS", (15, 34),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 220, 0), 2)
                cv2.rectangle(frame_x, (0, 0), (wx - 1, hx - 1), (255, 220, 0), 3)
            else:
                frame_x = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame_x, "EXIT CAMERA WAITING", (50, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Normalize height if resolutions differ
            he = frame_e.shape[0]
            hx = frame_x.shape[0]
            if he != hx:
                target_h = min(he, hx)
                we_new = int(frame_e.shape[1] * (target_h / he))
                wx_new = int(frame_x.shape[1] * (target_h / hx))
                frame_e = cv2.resize(frame_e, (we_new, target_h))
                frame_x = cv2.resize(frame_x, (wx_new, target_h))

            combined = np.hstack([frame_e, frame_x])
            cv2.imshow(window_name, combined)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
    except KeyboardInterrupt:
        print("\n[INFO] Monitor stopped by user (Ctrl+C).")
    finally:
        cap_entry.release()
        cap_exit.release()
        cv2.destroyAllWindows()
        print("[INFO] Cameras released successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="ParkTrack 360 — USB & Network Camera Test Utility")
    parser.add_argument("--list", action="store_true",
                        help="Scan and list all connected USB camera devices on Windows DirectShow")
    parser.add_argument("--dual", action="store_true",
                        help="Run dual camera mode (Entry + Exit webcams side-by-side)")
    parser.add_argument("--lane", choices=["entry", "exit"], default=None,
                        help="Test only the Entry or Exit lane camera")
    parser.add_argument("--source", type=str, default=None,
                        help="Direct camera source override (e.g., 0, 1, or URL)")
    parser.add_argument("--entry", type=str, default=None,
                        help="Entry camera source override")
    parser.add_argument("--exit", type=str, default=None,
                        help="Exit camera source override")
    args = parser.parse_args()

    if args.list:
        list_connected_cameras()
        return

    config = load_config()
    cam_cfg = config.get("camera", {})
    mode = cam_cfg.get("mode", "dual")

    # CLI direct source override
    if args.source is not None:
        source, is_url = parse_source(args.source)
        run_single_camera(source, is_url, "ParkTrack 360 - Custom Camera", cam_cfg)
        return

    # Specific lane test
    if args.lane:
        lane_cfg = cam_cfg.get(args.lane, {})
        source_val = getattr(args, args.lane) or lane_cfg.get("source", 0 if args.lane == "entry" else 1)
        source, is_url = parse_source(source_val)
        run_single_camera(source, is_url, f"ParkTrack 360 — {args.lane.upper()} Lane Camera", lane_cfg)
        return

    # Dual camera mode
    if args.dual or mode == "dual":
        entry_val = args.entry or cam_cfg.get("entry", {}).get("source", 0)
        exit_val = args.exit or cam_cfg.get("exit", {}).get("source", 1)
        success = run_dual_cameras(entry_val, exit_val, cam_cfg)
        if not success:
            print("\n[NOTE] Dual mode could not open both cameras. Falling back to single camera mode...")
            single_src = cam_cfg.get("single", {}).get("source", entry_val)
            source, is_url = parse_source(single_src)
            run_single_camera(source, is_url, "ParkTrack 360 — Single Camera (Fallback)", cam_cfg.get("single", {}))
        return

    # Single camera mode fallback
    single_cfg = cam_cfg.get("single", {})
    source_val = single_cfg.get("source", cam_cfg.get("source", 0))
    source, is_url = parse_source(source_val)
    run_single_camera(source, is_url, "ParkTrack 360 — Single Camera", single_cfg)

if __name__ == "__main__":
    main()
