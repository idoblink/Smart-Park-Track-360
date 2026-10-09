# Step 2 Report — Standalone Firmware

**Date:** 2026-10-09  
**Status:** Built and ready for hardware testing

---

## 📦 What Was Built

The complete modular firmware for the **ParkTrack 360** controller has been built in `firmware/parktrack360/`:

| Module | Files | Responsibility |
|---|---|---|
| **Main Sketch** | `parktrack360.ino` | Setup sequence, main non-blocking execution loop |
| **Config** | `config.h` | Central hardware pin mapping, timings, thresholds, addresses |
| **Secrets** | `secrets.h`, `secrets.example.h` | Wi-Fi credentials & server IP defaults (git-ignored) |
| **Sensors** | `sensors.h`, `sensors.cpp` | Non-blocking round-robin reader for 8× HC-SR04 with sliding median-of-3 filter |
| **Slots** | `slots.h`, `slots.cpp` | Baseline calibration, occupancy classification, debounce logic, and fault detection |
| **LEDs** | `leds.h`, `leds.cpp` | Active-LOW control of 16 slot LEDs across 2× PCF8574 expanders (`0x26`, `0x25`) |
| **Display** | `display.h`, `display.cpp` | 16×2 Character LCD controller (LiquidCrystal_I2C at `0x27`) with occupancy readouts |
| **Gates** | `gates.h`, `gates.cpp` | Non-blocking servo state machine (0° ➔ 90° gradual sweep, hold timer, safety refusal checks) |
| **Storage** | `storage.h`, `storage.cpp` | ESP32 Preferences (NVS) for persistent baselines, margins, servo angles, network configuration |
| **Networking** | `net.h`, `net.cpp` | Non-blocking Wi-Fi STA manager + WebSocket client protocol (`/ws/esp32`) |
| **Serial CLI** | `serial_cmd.h`, `serial_cmd.cpp` | Interactive command-line console over Serial (115200 baud) for diagnostics and manual controls |

---

## 🛠️ Required Arduino IDE Libraries

Ensure the following libraries are installed in **Arduino IDE Library Manager**:
1. **ESP32Servo** by Kevin Harrington
2. **LiquidCrystal_I2C** by Frank de Brabander (or Marco Schwartz)
3. **ArduinoJson** by Benoit Blanchon (Version 7.x)
4. **WebSockets** by Markus Sattler

---

## 🚀 How to Upload & Run Step 2

1. Connect your **ESP32 DevKit V1** to your computer via USB.
2. In Arduino IDE:
   - Select Board: **ESP32 Dev Module**
   - Select the active **COM Port**
3. Open `firmware/parktrack360/parktrack360.ino`.
4. Click **Upload** (`➔`).
5. Open the **Serial Monitor** and set baud rate to **115200**.
6. Press the **EN / RST** button on the ESP32.

---

## 📋 Interactive Serial Command Test Checklist

Type each command into the Serial Monitor input field at the top and press Enter:

### 1. `help`
Lists all available commands and their syntax.

### 2. `scan`
Scans the I²C bus. Should show:
- `0x25` (First Floor LEDs PCF8574)
- `0x26` (Ground Floor LEDs PCF8574)
- `0x27` (16x2 LCD backpack)

### 3. `status`
Displays real-time readings:
- Firmware version, uptime, calibration status
- Slot states (`VACANT`, `OCCUPIED`, `FAULT`, or `UNKNOWN`), distances, baselines
- Gate states, servo angles, hold times
- Wi-Fi status and link status

### 4. `calibrate`
- **Important:** Ensure all 8 parking slots are empty!
- Runs 15 rounds of ultrasonic measurements.
- Calculates and stores the empty baselines into ESP32 NVS.
- LCD will display `CALIBRATING...` followed by `CALIBRATION OK`.
- Slot LEDs will immediately turn **GREEN** (all 8 vacant).

### 5. `ledtest`
Steps through all 16 slot LEDs one-by-one to verify wiring and color mapping.

### 6. Test Real Car Occupancy
1. Place a toy car in slot **G1**:
   - Within ~0.5 s, G1 LED switches from **GREEN** to **RED**.
   - LCD updates to: `Occ:1  Free:7`.
2. Remove the toy car from **G1**:
   - G1 LED turns back to **GREEN**.
   - LCD updates to: `Occ:0  Free:8`.
3. Fill all slots or place obstacles in front of sensors:
   - When all 8 slots are occupied, LCD line 2 displays: `PARKING FULL`.

### 7. Test Barrier Gates via Serial
- `gate entry open`:
  - If parking is full or uncalibrated, gate **REFUSES** to open.
  - If parking has free space, gate sweeps from 0° ➔ 90°, holds for 5 seconds, and closes.
- `gate entry close`: Closes entry gate immediately.
- `gate exit open`: Sweeps exit gate 0° ➔ 90°, holds, and closes.
- `gate exit close`: Closes exit gate immediately.

### 8. Test Settings Persistence
- Set custom hold time: `hold 4000`
- Set custom margin: `margin 1.8`
- Type `reboot` and run `status`:
  - Notice your baselines and custom settings persisted across reboot!
