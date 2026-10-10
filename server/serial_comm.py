"""
ParkTrack 360 — server/serial_comm.py
Direct USB Serial communication with ESP32 (115200 baud).
Handles automatic COM port detection, reconnection, non-blocking reading,
and JSON command dispatching.
"""

import sys
import time
import json
import logging
import threading
from typing import Optional, Callable, Dict, Any
import serial
import serial.tools.list_ports

logger = logging.getLogger("parktrack.serial")

class ESP32SerialManager:
    def __init__(self, port: str = "auto", baudrate: int = 115200,
                 on_json: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_status_change: Optional[Callable[[bool], None]] = None):
        self.preferred_port = port
        self.baudrate = baudrate
        self.on_json = on_json
        self.on_status_change = on_status_change

        self.ser: Optional[serial.Serial] = None
        self.running = False
        self.connected = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def find_esp32_port(self) -> Optional[str]:
        """Finds active ESP32 COM port."""
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            return None

        # If user explicitly configured a specific port (e.g. COM3) and it exists:
        if self.preferred_port and self.preferred_port.lower() != "auto":
            for p in ports:
                if p.device.upper() == self.preferred_port.upper():
                    return p.device

        # Auto-detect CP210x, CH340, FTDI, or USB Serial device
        for p in ports:
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if any(k in desc or k in hwid for k in ["cp210", "ch340", "ch341", "ftdi", "uart", "usb-serial", "silicon labs"]):
                return p.device

        # Fallback to the first available COM port
        return ports[0].device

    def start(self):
        """Starts background reader thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ESP32SerialWorker")
        self._thread.start()
        logger.info("ESP32 USB Serial worker started.")

    def stop(self):
        """Stops background reader thread and closes port."""
        self.running = False
        self._close_port()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("ESP32 USB Serial worker stopped.")

    def _close_port(self):
        with self._lock:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.ser = None
            if self.connected:
                self.connected = False
                if self.on_status_change:
                    self.on_status_change(False)

    def _run_loop(self):
        while self.running:
            if not self.connected:
                port_name = self.find_esp32_port()
                if port_name:
                    try:
                        logger.info(f"Connecting to ESP32 on {port_name} at {self.baudrate} baud...")
                        ser = serial.Serial(port_name, self.baudrate, timeout=1.0)
                        time.sleep(0.2)  # Give time for DTR/RTS to settle
                        with self._lock:
                            self.ser = ser
                            self.connected = True
                        logger.info(f"[SUCCESS] Connected to ESP32 on USB Serial ({port_name})!")
                        if self.on_status_change:
                            self.on_status_change(True)

                        # Send initial hello_ack to wake up / acknowledge ESP32
                        self.send({"t": "hello_ack"})
                    except (serial.SerialException, OSError) as e:
                        logger.debug(f"Could not open {port_name}: {e}")
                        time.sleep(2.0)
                        continue
                else:
                    # No ESP32 COM port found yet; wait and retry
                    time.sleep(2.0)
                    continue

            # Read lines while connected
            try:
                line_bytes = self.ser.readline()
                if not line_bytes:
                    continue

                line_str = line_bytes.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                # Check if line is a JSON payload
                if line_str.startswith("{") and line_str.endswith("}"):
                    try:
                        data = json.loads(line_str)
                        if self.on_json:
                            self.on_json(data)
                    except Exception as e:
                        logger.warning(f"Malformed JSON from ESP32: {line_str} ({e})")
                else:
                    # Informational console message from ESP32 firmware
                    logger.info(f"[ESP32 Serial] {line_str}")

            except (serial.SerialException, OSError) as e:
                logger.warning(f"ESP32 USB Serial disconnected ({e}). Reconnecting...")
                self._close_port()
                time.sleep(1.0)

    def send(self, payload: Dict[str, Any]) -> bool:
        """Sends a JSON dictionary line to the ESP32 over serial."""
        with self._lock:
            if not self.ser or not self.ser.is_open:
                return False
            try:
                msg = json.dumps(payload) + "\n"
                self.ser.write(msg.encode("utf-8"))
                self.ser.flush()
                return True
            except Exception as e:
                logger.error(f"Failed to write to ESP32 serial: {e}")
                return False
