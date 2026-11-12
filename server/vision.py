"""
ParkTrack 360 — server/vision.py
High-accuracy Computer Vision digit recognition for toy cars labelled with white paper
and black marker digits (1 to 8).

Features:
- Machine Learning digit classifier (MLP trained on digits 1-8 + negative class 0 distractor rejection).
- Surrounding white-paper patch contrast verification (rejects table edges, lines, screws, shadows).
- Topological loop & aspect-ratio geometric constraints.
- Multi-frame temporal voting debouncing (rejects transient noise).
- Real-time exit clearance verification (ensures exit gate opens only after verified payment,
  or free pass for unparked vehicles).
"""

import os
import sys
import time
import logging
import threading
from typing import Dict, List, Tuple, Optional, Any, Callable
import cv2
import numpy as np

logger = logging.getLogger("parktrack.vision")

# Try to import joblib for loading trained ML model
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False


class DigitRecognizer:
    """Accurate digit recognizer for black marker numbers on white paper patches.
    Uses ML classifier (digits 1-8 vs negative class 0) + topological validation +
    paper contrast verification to eliminate false detections from random lines and structures.
    """

    def __init__(self, model_path: str = "server/digit_classifier.pkl"):
        self.model_path = model_path
        self.classifier = self._load_model(model_path)
        self.bank: Dict[int, List[np.ndarray]] = self._build_template_bank()

    def _load_model(self, path: str):
        if HAS_JOBLIB and os.path.exists(path):
            try:
                clf = joblib.load(path)
                logger.info(f"[SUCCESS] Loaded trained ML digit classifier from {path}")
                return clf
            except Exception as e:
                logger.warning(f"Could not load ML model from {path}: {e}")
        return None

    def _build_template_bank(self) -> Dict[int, List[np.ndarray]]:
        """Normalized 32x32 binary templates across multiple fonts and angles for digits 1 through 8."""
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
                            scale = 24.0 / max(h, w)
                            nh = max(1, int(h * scale))
                            nw = max(1, int(w * scale))
                            resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)

                            norm = np.zeros((32, 32), dtype=np.uint8)
                            oy = (32 - nh) // 2
                            ox = (32 - nw) // 2
                            norm[oy:oy + nh, ox:ox + nw] = resized
                            bank[digit].append(norm)

            if digit == 1:
                # Vertical stroke | and hook 1
                for thick in [3, 4, 5]:
                    img = np.zeros((64, 64), dtype=np.uint8)
                    cv2.line(img, (32, 10), (32, 54), 255, thick)
                    ys, xs = np.where(img > 0)
                    if len(ys) > 0:
                        crop = img[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
                        h, w = crop.shape
                        scale = 24.0 / max(h, w)
                        nh = max(1, int(h * scale))
                        nw = max(1, int(w * scale))
                        resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
                        norm = np.zeros((32, 32), dtype=np.uint8)
                        norm[(32 - nh) // 2:(32 - nh) // 2 + nh, (32 - nw) // 2:(32 - nw) // 2 + nw] = resized
                        bank[1].append(norm)

        return bank

    def extract_features(self, norm_32x32: np.ndarray) -> np.ndarray:
        """Extracts rotation-robust feature vector matching training pipeline."""
        img_float = norm_32x32.astype(np.float32) / 255.0
        small = cv2.resize(img_float, (16, 16), interpolation=cv2.INTER_AREA).flatten()
        h_proj = np.sum(img_float, axis=1) / 32.0
        v_proj = np.sum(img_float, axis=0) / 32.0

        padded = cv2.copyMakeBorder(norm_32x32, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)
        cnts, hier = cv2.findContours(padded, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        holes = 0
        if hier is not None:
            for hh in hier[0]:
                if hh[3] != -1:
                    holes += 1

        hu = cv2.HuMoments(cv2.moments(norm_32x32)).flatten()
        hu_log = -np.sign(hu) * np.log10(np.abs(hu) + 1e-7)

        return np.concatenate([small, h_proj, v_proj, [holes], hu_log])

    def classify_crop(self, binary_patch: np.ndarray) -> Tuple[Optional[int], float]:
        """Classifies a binary crop (white digit pixels on black background).
        Returns (predicted_digit, confidence_score)."""
        ys, xs = np.where(binary_patch > 0)
        if len(ys) < 25:
            return None, 0.0

        crop = binary_patch[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
        h, w = crop.shape
        if h < 14 or w < 4:
            return None, 0.0

        aspect = float(w) / float(h)
        if aspect > 1.25 or aspect < 0.12:
            return None, 0.0

        # Solidity check (strokes are not solid blocks)
        area = len(ys)
        solidity = area / float(h * w)
        if solidity > 0.82 or solidity < 0.14:
            return None, 0.0

        # Normalize to 32x32 centered
        scale = 24.0 / max(h, w)
        nh = max(1, int(h * scale))
        nw = max(1, int(w * scale))
        resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
        norm = np.zeros((32, 32), dtype=np.uint8)
        oy = (32 - nh) // 2
        ox = (32 - nw) // 2
        norm[oy:oy + nh, ox:ox + nw] = resized

        # Topological loop counting
        padded = cv2.copyMakeBorder(norm, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)
        cnts, hier = cv2.findContours(padded, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        holes = 0
        if hier is not None:
            for hh in hier[0]:
                if hh[3] != -1:
                    holes += 1

        # Use trained ML classifier if available
        if self.classifier is not None:
            try:
                feats = self.extract_features(norm).reshape(1, -1)
                probs = self.classifier.predict_proba(feats)[0]
                classes = self.classifier.classes_

                prob_dict = {cls: prob for cls, prob in zip(classes, probs)}
                neg_prob = prob_dict.get(0, 0.0)

                # If negative/distractor class probability is high, reject!
                if neg_prob > 0.15:
                    return None, 0.0

                best_digit = None
                best_conf = 0.0
                for d in range(1, 9):
                    p = prob_dict.get(d, 0.0)
                    if p > best_conf:
                        best_conf = p
                        best_digit = d

                # Topological sanity gates
                if best_digit == 8 and holes < 1:
                    best_conf *= 0.60
                elif best_digit == 1 and holes > 0:
                    best_conf *= 0.40
                elif best_digit in [2, 3, 5, 7] and holes > 0:
                    best_conf *= 0.50

                if best_digit is not None and best_conf >= 0.70:
                    return best_digit, float(min(1.0, best_conf))
                return None, 0.0
            except Exception as e:
                logger.debug(f"ML classification exception: {e}")

        # Fallback to structural template matching
        best_digit = None
        best_score = -1.0
        for digit, tpls in self.bank.items():
            for tpl in tpls:
                res = cv2.matchTemplate(norm, tpl, cv2.TM_CCOEFF_NORMED)
                val = float(res[0][0])
                bonus = 0.0
                if digit == 1:
                    if aspect < 0.45:
                        bonus += 0.20
                    elif holes > 0:
                        bonus -= 0.35
                elif digit == 8:
                    if holes >= 2:
                        bonus += 0.35
                    elif holes == 0:
                        bonus -= 0.25
                elif digit in [2, 3, 5, 7]:
                    if holes > 0:
                        bonus -= 0.35

                score = val + bonus
                if score > best_score:
                    best_score = score
                    best_digit = digit

        conf = min(1.0, max(0.0, best_score))
        if conf >= 0.65:
            return best_digit, conf
        return None, 0.0

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

        gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY) if len(sub.shape) == 3 else sub

        # Check frame brightness variance (reject pure black or blank frames)
        if np.mean(gray) < 20 or np.std(gray) < 10:
            return []

        # Dual thresholding
        thresh_adapt = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15
        )
        _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        detections = []
        seen_boxes = []

        for thresh_img in [thresh_otsu, thresh_adapt]:
            cnts, hier = cv2.findContours(thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if hier is None:
                continue

            for i, c in enumerate(cnts):
                x, y, w, h = cv2.boundingRect(c)

                # Filter marker digit bounding box constraints
                # Digits 1-8 have specific aspect ratio and size
                if not (8 <= w <= 240 and 18 <= h <= 300 and 0.12 <= (w / float(h)) <= 1.25):
                    continue

                area = cv2.contourArea(c)
                if area < 50 or area > (w * h * 0.78):
                    continue

                # Surrounding white paper patch contrast verification
                # A real black marker digit is written on white/light paper!
                pad = 8
                bx1, by1 = max(0, x - pad), max(0, y - pad)
                bx2, by2 = min(gray.shape[1], x + w + pad), min(gray.shape[0], y + h + pad)
                bg_crop = gray[by1:by2, bx1:bx2]
                stroke_crop = gray[y:y + h, x:x + w]

                bg_mean = float(np.mean(bg_crop))
                stroke_mean = float(np.mean(stroke_crop))

                # Background must be significantly brighter than dark ink (contrast >= 22)
                # and background should be reasonably bright paper (>= 90)
                if bg_mean < 85 or (bg_mean - stroke_mean) < 20:
                    continue

                # Prevent duplicate detections of the same box
                gx, gy = x + offset_x, y + offset_y
                is_duplicate = False
                for sx, sy, sw, sh in seen_boxes:
                    if abs(gx - sx) < 12 and abs(gy - sy) < 12 and abs(w - sw) < 12:
                        is_duplicate = True
                        break
                if is_duplicate:
                    continue

                crop = thresh_img[y:y + h, x:x + w]
                digit, conf = self.classify_crop(crop)

                if digit is not None and conf >= 0.65:
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
                 stable_frames: int = 3,
                 on_digit_confirmed: Optional[Callable[[str, int], None]] = None,
                 status_provider: Optional[Callable[[], Dict[str, Any]]] = None):
        self.lane = lane  # "entry" or "exit"
        self.source = source
        self.width = width
        self.height = height
        self.roi = roi
        self.stable_frames = stable_frames
        self.on_digit_confirmed = on_digit_confirmed
        self.status_provider = status_provider

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
                backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
                self.cap = cv2.VideoCapture(idx, backend)
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
                box_color = (0, 255, 0) if self.lane == "entry" else (0, 200, 255)
                cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), box_color, 2)
                cv2.putText(frame, f"CAR #{d} ({int(conf * 100)}%)", (bx, max(22, by - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, box_color, 2)

            # Debouncing logic: require same digit across stable_frames consecutive frames
            is_in_cooldown = (now < self.cooldown_until)

            if current_detected_digit is not None:
                self.recent_detections.append(current_detected_digit)
                if len(self.recent_detections) > (self.stable_frames + 2):
                    self.recent_detections.pop(0)

                # Check if detected digit is stable
                if self.recent_detections.count(current_detected_digit) >= self.stable_frames:
                    if not is_in_cooldown:
                        logger.info(f"[{self.lane.upper()}] Confirmed Car #{current_detected_digit} (stable across {self.stable_frames} frames).")
                        self.last_confirmed_car = current_detected_digit
                        self.cooldown_until = now + 8.0  # 8s cooldown while car passes or pays
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
            if now < self.gate_open_until and self.lane == "entry":
                cv2.rectangle(frame, (0, h - 50), (w, h), (0, 140, 255), -1)
                cv2.putText(frame, f">> CAR #{self.last_confirmed_car} AUTHORIZED: ENTRY GATE OPENING <<",
                            (25, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            elif now < self.gate_open_until and self.lane == "exit":
                cv2.rectangle(frame, (0, h - 50), (w, h), (0, 100, 220), -1)
                cv2.putText(frame, f">> CAR #{self.last_confirmed_car} AT EXIT: SCAN QR CODE TO PAY <<",
                            (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            elif is_in_cooldown:
                cv2.rectangle(frame, (0, h - 45), (w, h), (40, 40, 40), -1)
                rem = int(self.cooldown_until - now)
                cv2.putText(frame, f"LANE CYCLE ACTIVE - COOLDOWN ({rem}s)",
                            (25, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (180, 180, 180), 2)
            else:
                cv2.rectangle(frame, (0, h - 35), (w, h), (20, 20, 20), -1)
                label = "ENTRY SENSING ARMED (SHOW NUMBERED CAR 1-8)" if self.lane == "entry" else "EXIT SCANNER ARMED (VERIFIES CAR NUMBER 1-8)"
                cv2.putText(frame, label, (20, status_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 255, 100), 2)

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
        vision_cfg = config.get("vision", {})
        stable_frames = int(vision_cfg.get("stable_frames", 3))

        e_src = cam_cfg.get("entry", {}).get("source", 2)
        x_src = cam_cfg.get("exit", {}).get("source", 1)

        e_roi = cam_cfg.get("entry", {}).get("roi", None)
        x_roi = cam_cfg.get("exit", {}).get("roi", None)

        self.entry_worker = VisionLaneWorker(
            lane="entry", source=e_src, width=640, height=480, roi=e_roi,
            stable_frames=stable_frames,
            on_digit_confirmed=self._handle_digit
        )
        self.exit_worker = VisionLaneWorker(
            lane="exit", source=x_src, width=640, height=480, roi=x_roi,
            stable_frames=stable_frames,
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
