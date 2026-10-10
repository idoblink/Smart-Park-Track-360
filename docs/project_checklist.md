# ParkTrack 360 — Complete Project Roadmap & Implementation Checklist

This checklist tracks every milestone across hardware validation, embedded firmware, backend server development, web dashboard, automated billing/payment gateway integration, and computer vision recognition.

---

## 📌 Phase 1: Hardware Testing & Validation

Status: **COMPLETED ✅**

* [x] **ESP32 Module Verification (`t06_psram`)**
  * [x] Confirm ESP32 DevKit V1 has 0 bytes PSRAM (WROOM-32 module verified).
  * [x] Confirm GPIO16 and GPIO17 are free for ultrasonic sensing (F3 and F4 ECHO pins).
* [x] **I2C Bus Scan & Address Conflict Check (`t01_i2c_scan`)**
  * [x] Shared bus initialized on GPIO21 (SDA) and GPIO22 (SCL).
  * [x] 16x2 Character LCD backpack detected at `0x27` (all A0-A2 pads unbridged).
  * [x] Ground Floor LED expander PCF8574 detected at `0x26` (A0 pad bridged).
  * [x] First Floor LED expander PCF8574 detected at `0x25` (A1 pad bridged).
* [x] **Ultrasonic Sensor Bus Verification (`t02_hcsr04`)**
  * [x] Tested all 8 HC-SR04 sensors (G1–G4 and F1–F4) powered by external 5V rail.
  * [x] Verified 1kΩ / 2kΩ voltage dividers on all 8 ECHO lines to protect 3.3V ESP32 inputs.
  * [x] Confirmed live distance readings and obstacle detection.
* [x] **16 Slot LED Circuit Verification (`t03_leds`)**
  * [x] Verified active-LOW sink wiring on all 16 LEDs with 220Ω current-limiting resistors.
  * [x] Tested 0xAA pattern (All Vacant — all 8 Green LEDs ON, Red OFF).
  * [x] Tested 0x55 pattern (All Occupied — all 8 Red LEDs ON, Green OFF).
  * [x] Tested 0x00 (All ON) and 0xFF (All OFF).
  * [x] Verified individual walking sequence through all 16 pins across both expanders.
* [x] **Barrier Gate Servo Sweep Verification (`t04_servo`)**
  * [x] Verified Entry Servo PWM on GPIO23 (0° to 90° smooth sweep).
  * [x] Verified Exit Servo PWM on GPIO15 (0° to 90° smooth sweep).
  * [x] Identified and replaced defective servo motor on hardware.
  * [x] Connected 5V power to external supply with 470µF–1000µF smoothing capacitor.
* [x] **Integration Wiring Documentation**
  * [x] Created `complete_wiring.md` detailing every pin, rail, and connection without tables.
* [x] **Bill of Materials & Component Catalog**
  * [x] Created `components.md` detailing all sensors, ICs, actuators, camera research, and specs.

---

## 📌 Phase 2: Controller Firmware (Modular C++ Architecture)

Status: **FIRMWARE BUILT — PENDING HARDWARE TEST RUN ⏳**

* [x] **Central Configuration (`firmware/parktrack360/config.h`)**
  * [x] Defined all GPIO pin assignments, I2C addresses, timings, and thresholds.
* [x] **Persistent Storage (`firmware/parktrack360/storage.*`)**
  * [x] Implemented NVS (Preferences) storage for baselines, margin, servo angles, hold time, and Wi-Fi credentials.
* [x] **Ultrasonic Sensor Module (`firmware/parktrack360/sensors.*`)**
  * [x] Non-blocking round-robin reading of 8 sensors (spaced by 15 ms).
  * [x] Sliding median-of-3 filter per slot to reject ultrasonic noise.
* [x] **Slot State Manager (`firmware/parktrack360/slots.*`)**
  * [x] Multi-round baseline calibration routine (15 rounds with spread checks).
  * [x] Occupancy classification with 3-round debounce logic.
  * [x] Sensor fault detection (10 consecutive timeouts triggers FAULT state).
* [x] **Slot LED Driver (`firmware/parktrack360/leds.*`)**
  * [x] Active-LOW output updates to PCF8574 at `0x26` and `0x25`.
  * [x] State-driven color matching: Vacant = Green ON, Occupied = Red ON, Fault/Uncalibrated = OFF.
* [x] **16x2 LCD Display Driver (`firmware/parktrack360/display.*`)**
  * [x] Dynamic screen layout: `Occ: N  Free: M`, `PARKING FULL`, or `CALIBRATE`.
  * [x] Redraw optimization (only writes I2C when text changes).
* [x] **Servo Barrier Gate State Machine (`firmware/parktrack360/gates.*`)**
  * [x] Non-blocking gradual motion (2° every 15 ms).
  * [x] States: CLOSED ➔ OPENING ➔ OPEN (hold timer) ➔ CLOSING ➔ CLOSED.
  * [x] Safety interlocks: refuses entry if parking lot is full, uncalibrated, or link is down.
* [x] **Networking & Protocol Driver (`firmware/parktrack360/net.*`)**
  * [x] Wi-Fi STA client with automatic background reconnection.
  * [x] WebSocket client connected to `ws://<server_ip>:8000/ws/esp32`.
  * [x] Protocol JSON messaging: `hello`, `state` heartbeat (1s), `gate_result`, `cal_result`.
* [x] **Serial Command Interface (`firmware/parktrack360/serial_cmd.*`)**
  * [x] 115200 baud console commands: `help`, `status`, `calibrate`, `gate entry open/close`, `gate exit open/close`, `wifi`, `server`, `margin`, `angles`, `hold`, `scan`, `ledtest`, `reboot`.
* [x] **Main Sketch Orchestration (`firmware/parktrack360/parktrack360.ino`)**
  * [x] Setup sequence and non-blocking main loop tying all subsystems together.
* [ ] **Hardware Verification (`Test 6`)**
  * [ ] Flash `parktrack360.ino` via Arduino IDE.
  * [ ] Execute `calibrate` with all 8 slots empty.
  * [ ] Verify real toy car placement updates LEDs and LCD in under 0.5s.
  * [ ] Verify manual gate controls via Serial Monitor.

---

## 📌 Phase 3: Laptop Server & Communication Backend

Status: **COMPLETED ✅**

* [x] **Python Environment Setup**
  * [x] Python 3.11 installed, `requirements.txt` (FastAPI, Uvicorn, WebSockets, PyYAML, Pytest, HTTPX, Pydantic).
  * [x] Created `run_server.bat` (Windows one-click launcher) and `run_server.sh`.
  * [x] Created `server/config.yaml` with server port 8000, timing thresholds, lane parameters, and billing configuration.
* [x] **SQLite Database Engine (`server/db.py`)**
  * [x] `events` table: logs timestamps, type, car ID, slot ID, and detail messages.
  * [x] `visits` table: tracks car, entry/exit timestamps, inside dwell time, parked time, calculated fare, and payment status.
  * [x] `parkings` table: tracks slot sessions, start/end timestamps.
  * [x] `car_state` table: persistent car state (`OUTSIDE`, `ENTERED`, `PARKED`), assigned slot, visit ID.
  * [x] `meta` table: schema versioning and statistics epoch tracking.
* [x] **State Machine & Association Logic (`server/state.py`)**
  * [x] Global parking state: tracks free slots, occupied slots, distance reads, sensor faults.
  * [x] Car-to-slot heuristic association: automatically binds oldest entered car when slot sensor triggers.
  * [x] Gate authorization rules: enforces single-car state invariants, prevents duplicate entries, handles full-lot denials.
  * [x] Rollback handling: reverts vehicle state if gate operation fails or times out.
* [x] **ESP32 WebSocket Endpoint (`/ws/esp32`)**
  * [x] Handles `hello` handshake and issues `hello_ack`.
  * [x] Ingests 1s `state` telemetry heartbeats (slot states, gate states, distances, fault flags).
  * [x] Dispatches `gate` commands with tracking `req_id`.
  * [x] Dispatches `cmd` (`calibrate`) and processes results.
* [x] **Web UI WebSocket Endpoint (`/ws/ui`)**
  * [x] Broadcasts real-time JSON snapshot upon any hardware transition or operator command.
  * [x] Ingests operator manual commands (gate override, calibration trigger, slot reassignment).
* [x] **Offline Controller Simulator (`tools/fake_esp32.py`)**
  * [x] Interactive CLI simulator connecting to `ws://localhost:8000/ws/esp32` supporting `park <slot>`, `leave <slot>`, `fault <slot>`, `full`, `empty`, `drop`, and `reconnect`.
* [x] **Unit & Protocol Test Suite (`tests/`)**
  * [x] Comprehensive test suite (`test_state.py` and `test_protocol.py`) with 100% pass rate.

---

## 📌 Phase 4: Modern Web Dashboard (Frontend)

Status: **COMPLETED ✅**

* [x] **Rich User Interface Architecture (`server/static/`)**
  * [x] High-contrast, premium dark mode aesthetic with glassmorphism, responsive grid, and custom status pills.
  * [x] Clean vanilla CSS styling with zero external build tools required.
  * [x] Fully responsive layout for desktop laptops and mobile screens.
* [x] **Real-Time Interactive 2-Floor Slot Map**
  * [x] Visual 2-floor layout:
    * First Floor: **F1, F2, F3, F4**
    * Ground Floor: **G1, G2, G3, G4**
  * [x] **Exact Slot Status Display:**
    * Green badge = **Vacant / Free**
    * Red badge = **Occupied** (Displays parked Car #1 through #8)
    * Orange badge = **Sensor Fault**
    * Grey badge = **Stale / Offline**
  * [x] Live distance readout (cm) on each slot tile.
  * [x] Interactive slot assignment modal: click any slot to manually assign or release cars.
* [x] **System Status & Capacity Counters**
  * [x] Total Slots: `8`
  * [x] Occupied slots counter & Available slots counter with progress bar.
  * [x] ESP32 connection badge (`Online` / `Offline` with IP and firmware version).
  * [x] Calibration status badge (`Calibrated` / `Uncalibrated`).
* [x] **Barrier Gate Remote Controls**
  * [x] Entry Gate card: Current state (`Closed`, `Opening`, `Open`, `Closing`) with manual Open / Close buttons.
  * [x] Exit Gate card: Current state (`Closed`, `Opening`, `Open`, `Closing`) with manual Open / Close buttons.
  * [x] Maintenance controls: Calibrate Sensors button and Reset Daily Counters button.
* [x] **Dual Camera Feeds & Lane Status**
  * [x] Entry Lane video feed pane with camera state and last recognized vehicle.
  * [x] Exit Lane video feed pane with camera state and last recognized vehicle.
* [x] **Live Audit & Activity Log**
  * [x] Scrollable chronological event log (last 50 events, newest first).
  * [x] Color-coded events: Green (Entry), Red (Deny/Exit), Blue (Slot change), Purple (ESP32/System).

---

## 📌 Phase 5: Automated Billing & Payment Gateway Integration

Status: **COMPLETED ✅**

* [x] **Hourly Pricing Engine**
  * [x] Configurable base entry fee (`base_fee: 10 INR`).
  * [x] Configurable hourly rate (`hourly_rate: 20 INR/hr`, pro-rated per second).
  * [x] Configurable grace period (`grace_period_min: 5 min`).
* [x] **Active Parking Session & Live Fare Tracker**
  * [x] Real-time vehicle list table showing Car #, state, slot, entry timestamp, dwell timer (`HH:MM:SS`), and live accrued fare.
  * [x] Live dwell time tickers updating every second in the browser UI.
* [x] **Automated Exit Checkout & Payment Gateway Workflow**
  * [x] One-click "Checkout / Exit" trigger per active vehicle.
  * [x] **Dynamic QR Code Modal:** Displays UPI QR code (`upi://pay`), breakdown of dwell duration and total fare.
  * [x] **Operator Cashier Override:** "Confirm Cash Payment" and "Verify UPI Payment" buttons.
  * [x] Automated exit trigger: On payment confirmation, server marks visit completed, logs fare, and issues exit gate open command.
    * Payment Method (UPI / Card / Cash)
* [ ] **Financial & Revenue Analytics Dashboard Tab**
  * [ ] Daily, weekly, and monthly total revenue charts.
  * [ ] Total vehicles serviced today.
  * [ ] Average dwell time per vehicle.

---

## 📌 Phase 6: Single Webcam Vision Pipeline & YOLO Training

Status: **YET TO BE IMPLEMENTED ⏳**

* [ ] **Webcam Hardware & Lens Setup**
  * [ ] Mount camera overhead (25–35 cm) centered over Entry and Exit lanes.
  * [ ] Run `tools/camera_probe.py` to confirm 1280×720 MJPG capability.
  * [ ] Run `tools/focus_test.py` to tune manual focus ring for crisp tag sharpness at 30 px digit height.
  * [ ] Run `tools/roi_picker.py` to define Entry ROI and Exit ROI rectangles from the single frame.
* [ ] **Vehicle Tag Preparation**
  * [ ] Run `tools/make_tags.py` to generate printable sheet of bold tags (numbers 1 to 8).
  * [ ] Print on matte sticker paper and apply to the roofs of 8 toy cars.
* [ ] **Dataset Collection & Preparation**
  * [ ] Run `tools/collect.py` to record 500+ images (classes 1–8 plus negative empty-lane images).
  * [ ] Collect across varied lighting conditions and slight car orientations.
  * [ ] Annotate bounding boxes and create 70% Train / 15% Val / 15% Test split.
* [ ] **Model Training & CPU Optimization**
  * [ ] Train Ultralytics YOLO26n (or YOLO11n fallback) on the custom dataset.
  * [ ] Export model to ONNX / OpenVINO for fast CPU inference (target < 80 ms per ROI).
* [ ] **Stable-Read Filtering Engine**
  * [ ] Streak requirement: ≥ 5 consecutive frames detecting the identical class.
  * [ ] Confidence threshold: ≥ 0.70 confidence.
  * [ ] Single-class validation: reject if multiple conflicting classes are detected in the lane ROI.
  * [ ] Lane arming logic: 8-second cooldown after gate open, plus 1-second empty lane re-arm check.

---

## 📌 Phase 7: Full System Integration & Acceptance Testing

Status: **YET TO BE IMPLEMENTED ⏳**

* [ ] **End-to-End Entry Workflow**
  * [ ] Toy car drives to entry lane ➔ Camera recognizes Car #3 ➔ Server checks lot has space ➔ Server sends `gate entry open` ➔ Entry gate sweeps open ➔ Car enters slot G2 ➔ Sensor G2 detects car ➔ G2 LED turns RED ➔ LCD updates count ➔ Dashboard highlights G2 as occupied by Car #3.
* [ ] **End-to-End Exit Workflow**
  * [ ] Car #3 leaves slot G2 ➔ Sensor G2 detects vacant ➔ G2 LED turns GREEN ➔ Car drives to exit lane ➔ Exit camera recognizes Car #3 ➔ Fare calculated & payment completed ➔ Exit gate sweeps open ➔ Car departs ➔ Session finalized in database.
* [ ] **Full Lot Rejection Acceptance Test**
  * [ ] Occupy all 8 slots ➔ Next car arrives at entry ➔ Camera reads car ➔ System refuses entry ➔ LCD displays `PARKING FULL` ➔ Gate remains strictly closed.
* [ ] **Network Loss Fail-Safe Test**
  * [ ] Disconnect laptop Wi-Fi ➔ ESP32 detects link down ➔ Barrier gates lock closed for safety ➔ Standalone sensing and LEDs continue operating.
* [ ] **Persistence & Reconnection Test**
  * [ ] Power cycle ESP32 or restart server ➔ Baselines and active parking sessions restored accurately from database and NVS.
