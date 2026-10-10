# ParkTrack 360 — Live System Testing Guide (Final Integration Stage)

This guide covers the **active integration stage**: full wiring is completed, 2 USB webcams are connected, and the system is ready for firmware upload, portal verification, and real-world hardware validation.

---

## 📋 Current System State Overview

* **Wiring:** 100% complete according to [complete_wiring.md](file:///c:/Users/Hades/Documents/Smart-Park-Track-360/complete_wiring.md).
* **ESP32:** Connected via USB on **`COM3`** (`Silicon Labs CP210x`).
* **Cameras:** 2 USB webcams connected and verified:
  * **Entry Lane:** Camera Index **`1`**
  * **Exit Lane:** Camera Index **`2`**
  * *(Laptop Integrated Camera: Index `0`)*
* **Network & Host Server:**
  * Host Server IP: **`192.168.29.37`** (Port: `8000`)
  * Wi-Fi SSID configured in [firmware/parktrack360/secrets.h](file:///c:/Users/Hades/Documents/Smart-Park-Track-360/firmware/parktrack360/secrets.h).
* **Pricing & Rules:**
  * 100% Autonomous & Cashless (Zero Cash).
  * Flat **₹40** for the first hour (0–60 min), **+₹20/hr** for additional hours.

---

## ⚡ Stage 1: Upload Firmware to ESP32

### 1. Library Verification in Arduino IDE
Ensure these 4 libraries are installed in Arduino IDE (**Tools ➔ Manage Libraries...**):
1. **WebSockets** by *Markus Sattler*
2. **ESP32Servo** by *Kevin Harrington*
3. **LiquidCrystal_I2C** by *Frank de Brabander* (or *Marco Schwartz*)
4. **ArduinoJson** by *Benoit Blanchon* (v7.x)

### 2. Upload Firmware
1. Open Arduino IDE.
2. Open the main sketch: [firmware/parktrack360/parktrack360.ino](file:///c:/Users/Hades/Documents/Smart-Park-Track-360/firmware/parktrack360/parktrack360.ino).
3. Board: **ESP32 Dev Module**.
4. Port: **`COM3`**.
5. Click **Upload (`➔`)**.
6. Once uploaded, open **Serial Monitor** at **`115200 baud`**.
7. With all 8 slots empty, type:
   ```text
   calibrate
   ```
   * The 16×2 LCD will display `CALIBRATION OK`.
   * All 8 slot LEDs will turn **GREEN**.
   * LCD will display `Occ: 0  Free: 8`.

---

## 🌐 Stage 2: Start Host Server & Verify Web Portals

### 1. Launch Server
Double-click [run_server.bat](file:///c:/Users/Hades/Documents/Smart-Park-Track-360/run_server.bat) in the project root folder (or run `.\run_server.bat` in PowerShell).

The server will initialize FastAPI and automatically open your default browser to [http://localhost:8000](http://localhost:8000).

---

### 2. Web Portal Verification Checklist

Verify that all three web interfaces are operational:

#### A. Public User Dashboard — [http://localhost:8000](http://localhost:8000)
* [x] **Hero Header & Theme:** High-contrast royal architectural design inspired by *Heritage Hunt*.
* [x] **Key Stat Cards:**
  * **Total Slots:** Displays **`8`**
  * **Available Slots:** Updates live based on sensor occupancy
  * **Occupied Slots:** Updates live based on sensor occupancy
* [x] **Floor Layout Hierarchy:**
  * **Ground Floor (G1, G2, G3, G4)** is displayed on **TOP**.
  * **First Floor (F1, F2, F3, F4)** is displayed **BELOW**.
* [x] **Pricing Display:** Clearly displays ₹40 for 1st hour, +₹20/hr additional.
* [x] **Dedicated Checkout Button:** Prominent **"Proceed to Payment"** button that navigates directly to `/payment`.

#### B. Admin Operator Portal — [http://localhost:8000/admin](http://localhost:8000/admin)
* [x] **Authentication:** Accessing `/admin` redirects to [http://localhost:8000/admin/login](http://localhost:8000/admin/login) if unauthenticated.
  * Username: `admin`
  * Password: `admin360`
* [x] **ESP32 Link Monitor:** Displays **`ESP32: ONLINE`** with real-time heartbeat and firmware version `1.1.0`.
* [x] **Manual Gate Controls:** Working buttons for **"Open Entry Gate"** and **"Open Exit Gate"**.
* [x] **Sensor Calibration Trigger:** **"Calibrate Sensors"** button sends remote calibration command to ESP32.
* [x] **Live Audit Logs:** Table displaying real-time events (`entry`, `exit`, `payment`, `manual_gate`).

#### C. Autonomous Payment & Checkout Portal — [http://localhost:8000/payment](http://localhost:8000/payment)
* [x] **Cashless Policy:** Dedicated autonomous checkout — no cash payments accepted.
* [x] **Vehicle Lookup:** Select vehicle ID (Car 1 through 8).
* [x] **Fare Breakdown:** Real-time dwell duration and calculated fee in ₹ (INR).
* [x] **Dynamic SVG UPI QR Code:** Generates instant UPI payment QR code with amount pre-filled.
* [x] **Autonomous Gate Open:** Clicking **"Pay & Open Exit Gate"** validates payment and immediately signals the ESP32 to open the physical exit barrier.

---

## 📹 Stage 3: Dual USB Cameras Live Feed Check

Test that both cameras stream properly side-by-side:

```powershell
python tools/test_camera.py --dual
```

1. **Verify Split View:**
   * **Left Feed (Green Border):** Entry Lane Webcam (Index `1`).
   * **Right Feed (Cyan Border):** Exit Lane Webcam (Index `2`).
2. **Align Framing:**
   * Position the Entry webcam 20–30 cm facing/above the entry boom barrier.
   * Position the Exit webcam 20–30 cm facing/above the exit boom barrier.
3. **Focus Adjustment:**
   * Place a toy car at each gate and twist the lens focus ring until the number tag on the car roof is clear and sharp.
4. Press **`q`** or **`Ctrl+C`** to close the preview when aligned.

---

## 🚗 Stage 4: End-to-End Real Hardware Validation

Run through a complete parking cycle using a real toy car:

### Test Step 1: Slot Occupancy Detection
1. Place a toy car into slot **G1**:
   * **Hardware:** HC-SR04 sensor detects car roof height within 300 ms.
   * **Physical LED:** Slot G1 LED switches from **GREEN** to **RED**.
   * **16×2 LCD:** Updates to `Occ: 1  Free: 7`.
   * **Web Dashboard:** Slot G1 immediately turns **RED (Occupied)** on the screen.
2. Remove the toy car from slot **G1**:
   * Physical LED switches back to **GREEN**.
   * LCD updates to `Occ: 0  Free: 8`.
   * Web dashboard slot G1 turns **GREEN (Available)**.

---

### Test Step 2: Gate Servo Actuation
1. Go to the Admin Portal ([http://localhost:8000/admin](http://localhost:8000/admin)).
2. Click **"Open Entry Gate"**:
   * Physical Entry SG90 servo sweeps from 0° to 90°.
   * Stays open for 5 seconds.
   * Smoothly returns to 0° (Closed).
3. Click **"Open Exit Gate"**:
   * Physical Exit SG90 servo sweeps from 0° to 90°, holds 5 seconds, and closes.

---

### Test Step 3: Cashless Autonomous Checkout
1. Open the Payment Portal ([http://localhost:8000/payment](http://localhost:8000/payment)).
2. Select **Vehicle #1**.
3. View the fee calculation (e.g. ₹40 flat for the initial session).
4. Click **"Pay & Open Exit Gate"**:
   * Instant digital receipt is issued (`RCP-1-XXXXXX`).
   * The server sends the gate open trigger to the ESP32.
   * The physical exit barrier servo immediately opens to let the car leave!
