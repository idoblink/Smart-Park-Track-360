# Smart Park Track 360 (v1.1)

An automated, intelligent multi-floor parking management and vehicle tracking system powered by an **ESP32 microcontroller**, a **Python host server**, and a **single USB webcam computer vision pipeline**.

---

## 🏛️ System Architecture

```text
               Single Overhead USB Webcam
                           │ (USB MJPEG)
                           ▼
                  LAPTOP / HOST PC (Python)
          ┌─────────────────────────────────────────┐
          │  • Ultralytics YOLO Object Detector     │
          │  • FastAPI Server + SQLite Database     │
          │  • Modern 2-Floor Web Dashboard         │
          │  • Automated Billing & QR Payment Engine│
          └────────────────────┬────────────────────┘
                               │ WebSocket (JSON over 2.4 GHz Wi-Fi)
                               ▼
                        ESP32 DevKit V1
  ┌─────────────────────────────────────────────────────────┐
  │  • 8× HC-SR04 Ultrasonic Sensors (Slots G1–G4 & F1–F4)  │
  │  • 16× Slot LEDs via 2× PCF8574 Expanders (0x26, 0x25)  │
  │  • 1× 16×2 Character LCD Entrance Screen (0x27)         │
  │  • 2× Barrier Gate Servos (Entry: GPIO23, Exit: GPIO15) │
  │  • Non-blocking state machines & NVS persistent storage │
  └─────────────────────────────────────────────────────────┘
```

---

## 📚 Project Documentation & Quick Links

All project documentation is organized in the [`docs/`](docs/) directory:

| Document | Description |
|---|---|
| **[Complete Wiring Guide](docs/complete_wiring.md)** | Step-by-step pin-to-pin wiring instructions (table-free, short bullet points). |
| **[Component Catalog & Hardware Spec](docs/components.md)** | Full BOM, sensor specs, voltage requirements, and camera selection research. |
| **[Project Checklist & Roadmap](docs/project_checklist.md)** | Master milestone checklist detailing completed tasks and future phases. |
| **[Beginner's Hardware Testing Guide](docs/testing_guide.md)** | Step-by-step guides for running test sketches `t01` through `t06` and standalone `Test 6`. |
| **[Hardware Verification Record](docs/wiring.md)** | Log of actual test results and address confirmations from hardware tests. |
| **[Step 1 Hardware Report](docs/step-1-report.md)** | Summary report of Step 1 hardware checks. |
| **[Step 2 Standalone Firmware Report](docs/step-2-report.md)** | Overview of the modular C++ firmware architecture and test procedures. |
| **[Questions for the Owner](docs/questions.md)** | Hardware specifications and owner decisions log. |
| **[Build Specification v1.1](ParkTrack360_v1_1_Build_Spec.md)** | The comprehensive single source of truth for the entire project. |

---

## ⚡ Firmware Quick Start (Step 2 Standalone Mode)

The controller firmware is located in [`firmware/parktrack360/`](firmware/parktrack360/).

### 1. Required Arduino IDE Libraries
Install via **Arduino IDE Library Manager**:
* `ESP32Servo` by Kevin Harrington
* `LiquidCrystal_I2C` by Frank de Brabander (or Marco Schwartz)
* `ArduinoJson` by Benoit Blanchon (v7.x)
* `WebSockets` by Markus Sattler

### 2. Uploading Firmware
1. Open [`firmware/parktrack360/parktrack360.ino`](firmware/parktrack360/parktrack360.ino) in Arduino IDE.
2. Select Board: **ESP32 Dev Module**.
3. Select your ESP32's **COM Port**.
4. Click **Upload** (`➔`).
5. Open **Serial Monitor** at **115200 baud**.

### 3. Interactive Serial Commands
Type any of the following commands into the Serial Monitor:
* `help` — Show all available commands.
* `status` — Print real-time slot states, distances, baselines, and gate states.
* `calibrate` — Run 15-round baseline calibration (all 8 parking slots must be empty).
* `gate entry open` / `gate entry close` — Manually test entry barrier gate.
* `gate exit open` / `gate exit close` — Manually test exit barrier gate.
* `scan` — Scan the I²C bus for connected modules (`0x25`, `0x26`, `0x27`).
* `ledtest` — Step through all 16 slot LEDs one-by-one.
* `reboot` — Soft-reset the ESP32.

---

## 🔮 Upcoming Phases (In Progress)

1. **Python Host Server (FastAPI + SQLite):** Vehicle session tracking, live state synchronization, and WebSocket protocol.
2. **Modern Web Dashboard:** Visual 2-floor interactive slot grid (F1–F4, G1–G4), real-time occupancy counters, live camera feeds, and manual gate controls.
3. **Automated Billing & Payment Gateway:** Hourly parking rate engine, live dwell-time cost ticker, exit fee calculator, and dynamic UPI / QR checkout modal.
4. **Computer Vision (YOLO):** Overhead webcam digit detection (classes 1–8) for automatic entry and exit authorization.
