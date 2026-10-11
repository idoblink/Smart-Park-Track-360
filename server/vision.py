"""
ParkTrack 360 — server/vision.py
High-speed Computer Vision digit recognition for toy cars labelled with white paper
and black marker digits (1 to 8).

Manages dual USB webcams (Entry Lane & Exit Lane), recognizes digits via
multi-scale template matching + topological stroke/hole analysis, confirms detections,
and automatically opens the servo barrier gates to 180 degrees.
"""

import time
import logging
import threading
from typing import Dict, List, Tuple, Optional, Any, Callable
import cv2
import numpy as np

logger = logging.getLogger("parktrack.vision")


class DigitRecognizer:
    """Robust digit recognizer for black marker numbers on white paper patches."""

    def __init__(self):
        self.bank: Dict[int, List[np.ndarray]] = self._build_template_bank()

    def _build_template_bank(self) -> Dict[int, List[np.ndarray]]:
        """Pre-computes normalized 32x32 binary templates across multiple fonts,
        weights, and subtle angles for digits 1 through 8."""
        bank: Dict[int, List[np.ndarray]] = {}
        fonts = [
            cv2.FONT_HERSHEY_SIMPLEX,
            cv2.FONT_HERSHEY_DUPLEX,
            cv2.FONT_HERSHEY_COMPLEX,
            cv2.FONT_HERSHEY_TRIPLEX
        ]
        thicknesses = [2, 3, 4]
        angles = [-8, 0, 8]

        for digit in range(1, 9):
            bank[digit] = []
            for font in fonts:
                for thickness in thicknesses:
                    for angle in angles:
                        img = np.zeros((64, 64), dtype=np.uint8)
                        text = str(digit)
                        (tw, th), _ = cv2.getTextSize(text, font, 1.4, thickness)
                        tx = (64 - tw) // 2
                        ty = (64 + th) // 2
                        cv2.putText(img, text, (tx, ty), font, 1.4, 255, thickness)

                        if angle != 0:
                            M = cv2.getRotationMatrix2D((32, 32), angle, 1.0)
                            img = cv2.warpAffine(img, M, (64, 64))

                        ys, xs = np.where(img > 0)
                        if len(ys) > 0:
                            crop = img[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
                            h, w = crop.shape
                            scale = 26.0 / max(h, w)
                            nh = max(1, int(h * scale))
                            nw = max(1, int(w * scale))
                            resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)

                            norm = np.zeros((32, 32), dtype=np.uint8)
                            oy = (32 - nh) // 2
                            ox = (32 - nw) // 2
                            norm[oy:oy + nh, ox:ox + nw] = resized
                            bank[digit].append(norm)

            # For digit 1, also include handwritten marker variants:
            # 1. Plain vertical stroke |
            # 2. Classic marker 1 (top slant hook, vertical stem, horizontal bottom foot)
            if digit == 1:
                for thick in [3, 4, 5]:
                    for angle in [-6, 0, 6]:
                        # Plain vertical line
                        img = np.zeros((64, 64), dtype=np.uint8)
                        cv2.line(img, (32, 10), (32, 54), 255, thick)
                        if angle != 0:
                            M = cv2.getRotationMatrix2D((32, 32), angle, 1.0)
                            img = cv2.warpAffine(img, M, (64, 64))
                        ys, xs = np.where(img > 0)
                        if len(ys) > 0:
                            crop = img[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
                            h, w = crop.shape
                            scale = 26.0 / max(h, w)
                            nh = max(1, int(h * scale))
                            nw = max(1, int(w * scale))
                            resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
                            norm = np.zeros((32, 32), dtype=np.uint8)
                            norm[(32 - nh) // 2:(32 - nh) // 2 + nh, (32 - nw) // 2:(32 - nw) // 2 + nw] = resized
                            bank[1].append(norm)

                        # Classic marker 1 with hook and bottom foot
                        img2 = np.zeros((64, 64), dtype=np.uint8)
                        cv2.line(img2, (34, 12), (34, 52), 255, thick)
                        cv2.line(img2, (20, 24), (34, 12), 255, thick)
                        cv2.line(img2, (18, 52), (50, 52), 255, thick)
                        if angle != 0:
                            M = cv2.getRotationMatrix2D((32, 32), angle, 1.0)
                            img2 = cv2.warpAffine(img2, M, (64, 64))
                        ys, xs = np.where(img2 > 0)
                        if len(ys) > 0:
                            crop = img2[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
                            h, w = crop.shape
                            scale = 26.0 / max(h, w)
                            nh = max(1, int(h * scale))
                            nw = max(1, int(w * scale))
                            resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
                            norm = np.zeros((32, 32), dtype=np.uint8)
                            norm[(32 - nh) // 2:(32 - nh) // 2 + nh, (32 - nw) // 2:(32 - nw) // 2 + nw] = resized
                            bank[1].append(norm)

        logger.info(f"Built digit template bank: {len(bank)} digits (1-8), {sum(len(v) for v in bank.values())} glyphs.")
        return bank

    def classify_crop(self, binary_patch: np.ndarray) -> Tuple[Optional[int], float]:
        """Classifies a binary crop (white digit pixels on black background).
        Returns (predicted_digit, confidence_score)."""
        ys, xs = np.where(binary_patch > 0)
        if len(ys) < 20:
            return None, 0.0

        crop = binary_patch[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
        h, w = crop.shape
        if h < 12 or w < 3:
            return None, 0.0

        aspect = float(w) / float(h)

        # Topological feature extraction: holes & hole vertical center (with black border padding)
        padded = cv2.copyMakeBorder(crop, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=0)
        cnts, hier = cv2.findContours(padded, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        holes = 0
        hole_y_rel = 0.5
        min_hole_area = 0.02 * (h * w)
        if hier is not None:
            for i, hh in enumerate(hier[0]):
                if hh[3] != -1 and cv2.contourArea(cnts[i]) >= min_hole_area:  # Real loop, not tiny ink grain
                    holes += 1
                    M = cv2.moments(cnts[i])
                    if M["m00"] > 0:
                        hole_y_rel = ((M["m01"] / M["m00"]) - 4) / float(h)

        # Normalize to 32x32 centered
        scale = 26.0 / max(h, w)
        nh = max(1, int(h * scale))
        nw = max(1, int(w * scale))
        resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
        norm = np.zeros((32, 32), dtype=np.uint8)
        oy = (32 - nh) // 2
        ox = (32 - nw) // 2
        norm[oy:oy + nh, ox:ox + nw] = resized

        best_digit = None
        best_score = -1.0

        for digit, tpls in self.bank.items():
            for tpl in tpls:
                res = cv2.matchTemplate(norm, tpl, cv2.TM_CCOEFF_NORMED)
                val = float(res[0][0])

                # Topological bonuses & structural consistency checks
                bonus = 0.0
                if digit == 1:
                    if aspect < 0.45:
                        bonus += 0.25
                    elif holes > 0:
                        bonus -= 0.30

                elif digit == 8:
                    if holes >= 2:
                        bonus += 0.35
                    elif holes == 1:
                        bonus += 0.10
                    elif holes == 0:
                        bonus -= 0.20

                elif digit == 6:
                    if holes == 1 and hole_y_rel > 0.40:
                        bonus += 0.30
                    elif holes == 0:
                        bonus -= 0.15

                elif digit == 4:
                    if holes == 1 or aspect > 0.50:
                        bonus += 0.10

                elif digit in [2, 3, 5, 7]:
                    if holes == 0:
                        bonus += 0.05
                    else:
                        bonus -= 0.30

                score = val + bonus
                if score > best_score:
                    best_score = score
                    best_digit = digit

        return best_digit, min(1.0, max(0.0, best_score))

    def detect_digits(self, frame: np.ndarray, roi: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Detects and classifies black marker digits on white paper in frame/ROI.
        Returns list of detections: [{'digit': d, 'conf': score, 'box': (x,y,w,h)}]."""
        if frame is None or frame.size == 0:
            return []

        h_full, w_full = frame.shape[:2]
        if roi and len(roi) == 4:
            rx, ry, rw, rh = roi
            rx = max(0, min(rx, w_full - 1))
            ry = max(0, min(ry, h_full - 1))
            rw = min(rw, w_full - rx)
            rh = min(rh, h_full - ry)
            sub = frame[ry:ry + rh, rx:rx + rw]
            offset_x, offset_y = rx, ry
        else:
            sub = frame
            offset_x, offset_y = 0, 0

        gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)

        # Dual thresholding: Adaptive Gaussian + Otsu
        thresh_adapt = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15
        )
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        detections = []
        seen_boxes = []

        for thresh_img in [thresh_adapt, thresh_otsu]:
            cnts, hier = cv2.findContours(thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if hier is None:
                continue

            for i, c in enumerate(cnts):
                x, y, w, h = cv2.boundingRect(c)

                # Filter marker digit bounding box constraints
                if not (10 <= w <= 260 and 18 <= h <= 320 and 0.15 <= (w / h) <= 1.35):
                    continue

                area = cv2.contourArea(c)
                if area < 60 or area > (w * h * 0.90):
                    continue

                # Check surrounding background (white paper should be brighter than stroke)
                pad = 8
                bx1, by1 = max(0, x - pad), max(0, y - pad)
                bx2, by2 = min(gray.shape[1], x + w + pad), min(gray.shape[0], y + h + pad)
                bg_crop = gray[by1:by2, bx1:bx2]
                stroke_crop = gray[y:y + h, x:x + w]

                bg_mean = float(np.mean(bg_crop))
                stroke_mean = float(np.mean(stroke_crop))

                # White paper should have brightness >= 110, and contrast difference >= 20
                if bg_mean < 100 or (bg_mean - stroke_mean) < 18:
                    continue

                # Prevent duplicate detections of the same box
                gx, gy = x + offset_x, y + offset_y
                is_duplicate = False
                for sx, sy, sw, sh in seen_boxes:
                    if abs(gx - sx) < 15 and abs(gy - sy) < 15 and abs(w - sw) < 15:
                        is_duplicate = True
                        break
                if is_duplicate:
                    continue

                crop = thresh_img[y:y + h, x:x + w]
                digit, conf = self.classify_crop(crop)

                if digit is not None and conf >= 0.60:
                    seen_boxes.append((gx, gy, w, h))
                    detections.append({
                        "digit": digit,
                        "conf": conf,
                        "box": (gx, gy, w, h)
                    })

        # Sort by confidence descending
        detections.sort(key=lambda d: d["conf"], reverse=True)
        return detections


class VisionLaneWorker:
    """Worker for a single camera lane (Entry or Exit)."""

    def __init__(self, lane: str, source: Any, width: int = 640, height: int = 480,
                 roi: Optional[List[int]] = None,
                 on_digit_confirmed: Optional[Callable[[str, int], None]] = None):
        self.lane = lane  # "entry" or "exit"
        self.source = source
        self.width = width
        self.height = height
        self.roi = roi
        self.on_digit_confirmed = on_digit_confirmed

        self.recognizer = DigitRecognizer()
        self.cap: Optional[cv2.VideoCapture] = None
        self.running = False
        self._thread: Optional[threading.Thread] = None

        # Frame buffers (thread-safe)
        self._lock = threading.Lock()
        self.latest_raw_frame: Optional[np.ndarray] = None
        self.latest_annotated_jpeg: Optional[bytes] = None

        # State tracking
        self.cooldown_until = 0.0
        self.last_confirmed_car: Optional[int] = None
        self.recent_detections: List[int] = []
        self.gate_open_until = 0.0
        self.fps = 0.0

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"Vision-{self.lane}")
        self._thread.start()
        logger.info(f"Vision lane [{self.lane}] worker started (source={self.source}).")

    def stop(self):
        self.running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info(f"Vision lane [{self.lane}] worker stopped.")

    def _open_camera(self) -> bool:
        try:
            if isinstance(self.source, int) or str(self.source).isdigit():
                idx = int(self.source)
                self.cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            else:
                self.cap = cv2.VideoCapture(str(self.source))

            if self.cap and self.cap.isOpened():
                logger.info(f"[SUCCESS] Camera for lane [{self.lane}] opened on source {self.source}.")
                return True
        except Exception as e:
            logger.error(f"Error opening camera for [{self.lane}]: {e}")
        return False

    def _make_standby_frame(self, message: str) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        color = (0, 200, 100) if self.lane == "entry" else (240, 180, 0)
        cv2.rectangle(frame, (0, 0), (self.width - 1, self.height - 1), color, 2)
        cv2.putText(frame, f"PARKTRACK 360 - {self.lane.upper()} CAMERA", (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
        cv2.putText(frame, message, (30, self.height // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        cv2.putText(frame, f"Source: {self.source} | Dual USB Mode", (30, self.height - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (140, 140, 140), 1)
        return frame

    def _run(self):
        t_prev = time.time()

        while self.running:
            if not self.cap or not self.cap.isOpened():
                if not self._open_camera():
                    standby = self._make_standby_frame(f"Connecting to Camera Index {self.source}...")
                    _, buf = cv2.imencode(".jpg", standby, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    with self._lock:
                        self.latest_annotated_jpeg = buf.tobytes()
                    time.sleep(2.0)
                    continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                standby = self._make_standby_frame("Waiting for Video Frames...")
                _, buf = cv2.imencode(".jpg", standby, [cv2.IMWRITE_JPEG_QUALITY, 75])
                with self._lock:
                    self.latest_annotated_jpeg = buf.tobytes()
                time.sleep(0.05)
                continue

            now = time.time()
            dt = max(1e-5, now - t_prev)
            t_prev = now
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)

            # Digit detection
            detections = self.recognizer.detect_digits(frame, self.roi)

            # Draw lane header
            h, w = frame.shape[:2]
            header_color = (25, 75, 25) if self.lane == "entry" else (70, 50, 20)
            text_color = (0, 255, 120) if self.lane == "entry" else (255, 220, 0)

            cv2.rectangle(frame, (0, 0), (w, 45), header_color, -1)
            cv2.putText(frame, f"[{self.lane.upper()} LANE] Cam {self.source} | {self.fps:.1f} FPS",
                        (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

            # Draw ROI boundary if configured
            if self.roi and len(self.roi) == 4:
                rx, ry, rw, rh = self.roi
                cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (180, 180, 180), 1)

            # Process detected digits
            current_detected_digit = None
            if detections:
                top = detections[0]
                d = top["digit"]
                conf = top["conf"]
                bx, by, bw, bh = top["box"]

                current_detected_digit = d

                # Draw bounding box on detected digit
                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
                cv2.putText(frame, f"CAR {d} ({int(conf * 100)}%)", (bx, max(20, by - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

            # Debouncing logic: require same digit across 2 consecutive frames
            is_in_cooldown = (now < self.cooldown_until)

            if current_detected_digit is not None:
                self.recent_detections.append(current_detected_digit)
                if len(self.recent_detections) > 4:
                    self.recent_detections.pop(0)

                # Check if detected digit is stable (at least 2 occurrences in recent history)
                if self.recent_detections.count(current_detected_digit) >= 2:
                    if not is_in_cooldown:
                        logger.info(f"[{self.lane.upper()}] Confirmed Car #{current_detected_digit}! Triggering 180° gate.")
                        self.last_confirmed_car = current_detected_digit
                        self.cooldown_until = now + 8.0  # 8s cooldown while car passes
                        self.gate_open_until = now + 5.0
                        self.recent_detections.clear()

                        if self.on_digit_confirmed:
                            try:
                                self.on_digit_confirmed(self.lane, current_detected_digit)
                            except Exception as e:
                                logger.error(f"Error invoking digit confirmed callback: {e}")
            else:
                if len(self.recent_detections) > 0:
                    self.recent_detections.pop(0)

            # HUD Status Display
            status_y = h - 20
            if now < self.gate_open_until:
                cv2.rectangle(frame, (0, h - 50), (w, h), (0, 140, 255), -1)
                cv2.putText(frame, f">> CAR {self.last_confirmed_car} DETECTED: SERVO GATE OPEN 90° <<",
                            (25, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            elif is_in_cooldown:
                cv2.rectangle(frame, (0, h - 45), (w, h), (40, 40, 40), -1)
                rem = int(self.cooldown_until - now)
                cv2.putText(frame, f"GATE CYCLE COMPLETE - COOLDOWN ({rem}s)",
                            (25, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (180, 180, 180), 2)
            else:
                cv2.rectangle(frame, (0, h - 35), (w, h), (20, 20, 20), -1)
                cv2.putText(frame, "STATUS: ARMED (SHOW NUMBERED CAR 1-8)",
                            (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 2)

            # Encode annotated frame to JPEG for dashboard live feed
            _, jpeg_buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            with self._lock:
                self.latest_raw_frame = frame
                self.latest_annotated_jpeg = jpeg_buf.tobytes()

            time.sleep(0.03)  # ~30 FPS throttle

        if self.cap:
            self.cap.release()
            self.cap = None

    def get_frame_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self.latest_annotated_jpeg


class VisionManager:
    """Manages both Entry and Exit Vision lane workers."""

    def __init__(self, config: Dict[str, Any], on_car_event: Callable[[str, int], None]):
        self.config = config
        self.on_car_event = on_car_event

        cam_cfg = config.get("camera", {})
        e_src = cam_cfg.get("entry", {}).get("source", 1)
        x_src = cam_cfg.get("exit", {}).get("source", 2)

        e_roi = cam_cfg.get("entry", {}).get("roi", None)
        x_roi = cam_cfg.get("exit", {}).get("roi", None)

        self.entry_worker = VisionLaneWorker(
            lane="entry", source=e_src, width=640, height=480, roi=e_roi,
            on_digit_confirmed=self._handle_digit
        )
        self.exit_worker = VisionLaneWorker(
            lane="exit", source=x_src, width=640, height=480, roi=x_roi,
            on_digit_confirmed=self._handle_digit
        )

    def _handle_digit(self, lane: str, car_id: int):
        self.on_car_event(lane, car_id)

    def start(self):
        self.entry_worker.start()
        self.exit_worker.start()

    def stop(self):
        self.entry_worker.stop()
        self.exit_worker.stop()

    def get_jpeg(self, lane: str) -> Optional[bytes]:
        if lane == "entry":
            return self.entry_worker.get_frame_jpeg()
        elif lane == "exit":
            return self.exit_worker.get_frame_jpeg()
        return None
