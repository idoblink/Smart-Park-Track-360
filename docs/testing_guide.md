# Complete Beginner's Hardware Testing Guide for Smart Park Track 360 (16x2 LCD Version)

Welcome! This guide explains **step-by-step** how to test every hardware part of your parking model. You don't need any prior coding experience—just follow these instructions carefully!

---

## 🛠️ Step 0: Software Setup (Do This Once)

Before uploading any test code, prepare your computer:

### 1. Download and Install Arduino IDE
1. Download **Arduino IDE 2.x** from the official website: [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)
2. Install it on your computer using default settings.

### 2. Install ESP32 Board Package
1. Open **Arduino IDE**.
2. Click on **File** ➔ **Preferences** (or press `Ctrl + ,`).
3. Find the box named **Additional Boards Manager URLs**.
4. Paste this link into that box:
   ```text
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
5. Click **OK**.
6. On the left sidebar of Arduino IDE, click the **Boards Manager** icon (circuit board icon).
7. In the search bar, type `esp32`.
8. Find **esp32 by Espressif Systems** and click **Install**. Wait until the installation finishes.

### 3. Install Required Libraries
1. On the left sidebar of Arduino IDE, click the **Library Manager** icon (stack of books icon).
2. Install the following libraries:
   - **ESP32Servo** by Kevin Harrington
   - **LiquidCrystal_I2C** by Frank de Brabander (or Marco Schwartz)
   - **ArduinoJson** by Benoit Blanchon (v7.x)

---

## ⚙️ How to Upload Code to ESP32

Whenever you test a sketch, follow these exact steps:

1. Connect your **ESP32 board to your computer** using a micro-USB cable.
2. In Arduino IDE, go to **Tools** ➔ **Board** ➔ **esp32** ➔ select **ESP32 Dev Module** (do NOT select ESP32S2, ESP32S3, ESP32C3, etc. Select exact name: **ESP32 Dev Module**).
3. Go to **Tools** ➔ **Port** ➔ select the COM port corresponding to your ESP32 (e.g., `COM3`, `COM4`).
   - ⚠️ **If "Port" is greyed out:** Check USB data cable, try another USB port, or install CP210x/CH340 drivers.
4. Click **File** ➔ **Open** ➔ navigate to the test file (e.g., `firmware/tests/t06_psram/t06_psram.ino`).
5. Click the **Upload** button (the green arrow `➔` icon at top left).
6. Wait for `Done uploading`.
7. Click the **Serial Monitor** icon at top right (magnifying glass icon).
8. **CRITICAL:** Set the Baud Rate in the Serial Monitor to **115200**.

---

## 🛠️ Address Setup for 3x PCF8574 Modules (Confirmed & Tested)

Your **3 PCF8574 modules** share the same I²C bus (SDA=GPIO21, SCL=GPIO22):

1. **PCF8574 #1 (16x2 LCD Backpack):**
   - Leave `A0 A1 A2` un-bridged (default). Address = **`0x27`**.
2. **PCF8574 #2 (Ground Floor Slot LEDs):**
   - Solder blob across **`A0`** pads. Address = **`0x26`**.
3. **PCF8574 #3 (First Floor Slot LEDs):**
   - Solder blob across **`A1`** pads. Address = **`0x25`**.

---

## 🧪 Test 1: Check ESP32 Module Type (`t06_psram`) — PASSED! ✅

- **Goal:** Confirm ESP32 is WROOM module (0 bytes PSRAM).  
- **Status:** **PASSED** (PSRAM Size: 0 bytes, WROOM module OK — GPIO16/17 available for F3 & F4 sensors).

---

## 🧪 Test 2: Scan I²C Devices (`t01_i2c_scan`) — PASSED! ✅

- **Goal:** Detect all 3 I²C modules on the shared bus.
- **Status:** **PASSED** (Found all 3 devices cleanly: `0x25`, `0x26`, `0x27`).

---

## 🧪 Test 3: Test 8 Ultrasonic Sensors (`t02_hcsr04`) — PASSED! ✅

- **Goal:** Connect all 8 HC-SR04 ultrasonic sensors using assigned breadboard rows for exact resistor junctions.
- **Status:** **PASSED** (All 8 sensors G1–G4 and F1–F4 reading live distances cleanly!).

---

## 🧪 Test 4: Test 16 Slot LEDs (`t03_leds`) — PASSED! ✅

- **Goal:** Test all 16 slot LEDs (8 Green + 8 Red) using both PCF8574 expanders.
- **Status:** **PASSED** (Both expanders `0x26` and `0x25` walked through all 16 LEDs cleanly!).

---

### 💡 Understanding "Active-LOW" LED Wiring

The PCF8574 expander chip is designed to **sink current** (pull to Ground). That means:
- The LED's **Anode (long leg, +)** connects to **ESP32 3.3V Rail**.
- The LED's **Cathode (short leg, -)** connects through a **220Ω resistor** (Red-Red-Brown-Gold) to the **PCF8574 pin (P0..P7)**.
- When the code sends a **0 (LOW)** to a pin, current flows into the PCF8574 pin and the LED turns **ON**!
- When the code sends a **1 (HIGH)** to a pin, the LED turns **OFF**.

---

### 🔌 Part 1: Power & I²C Connections for the 2 LED Expanders

1. **Ground Floor Expander (PCF8574 #2, Address `0x26` — A0 bridged):**
   - Connect **VCC** pin ➔ ESP32 **3.3V Rail**.
   - Connect **GND** pin ➔ ESP32 **GND Rail**.
   - Connect **SDA** pin ➔ ESP32 **GPIO 21**.
   - Connect **SCL** pin ➔ ESP32 **GPIO 22**.

2. **First Floor Expander (PCF8574 #3, Address `0x25` — A1 bridged):**
   - Connect **VCC** pin ➔ ESP32 **3.3V Rail**.
   - Connect **GND** pin ➔ ESP32 **GND Rail**.
   - Connect **SDA** pin ➔ ESP32 **GPIO 21**.
   - Connect **SCL** pin ➔ ESP32 **GPIO 22**.

---

### 📍 Part 2: Step-by-Step Connection Instructions for All 16 LEDs

---

#### 🟢 Ground Floor Slot LEDs (Connected to PCF8574 #2 at `0x26`)

1. **Slot G1 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P0** on Expander `0x26`.

2. **Slot G1 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P1** on Expander `0x26`.

3. **Slot G2 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P2** on Expander `0x26`.

4. **Slot G2 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P3** on Expander `0x26`.

5. **Slot G3 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P4** on Expander `0x26`.

6. **Slot G3 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P5** on Expander `0x26`.

7. **Slot G4 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P6** on Expander `0x26`.

8. **Slot G4 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P7** on Expander `0x26`.

---

#### 🔵 First Floor Slot LEDs (Connected to PCF8574 #3 at `0x25`)

1. **Slot F1 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P0** on Expander `0x25`.

2. **Slot F1 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P1** on Expander `0x25`.

3. **Slot F2 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P2** on Expander `0x25`.

4. **Slot F2 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P3** on Expander `0x25`.

5. **Slot F3 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P4** on Expander `0x25`.

6. **Slot F3 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P5** on Expander `0x25`.

7. **Slot F4 Green LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P6** on Expander `0x25`.

8. **Slot F4 Red LED:**
   - Plug **Anode (long leg, +)** into the **ESP32 3.3V Rail**.
   - Plug **Cathode (short leg, -)** into a 220Ω resistor leg.
   - Connect the other leg of that 220Ω resistor directly to **Pin P7** on Expander `0x25`.

---

### 🚀 Step-by-Step Instructions to Run Test 4

1. Connect ESP32 to laptop via USB.
2. Open **Arduino IDE**.
3. Go to **File** ➔ **Open** ➔ navigate to `firmware/tests/t03_leds/t03_leds.ino`.
4. Click **Upload** (`➔`).
5. Open **Serial Monitor** (115200 baud).
6. Press **EN / RST** button on ESP32 once.

---

### 👁️ What to Watch During Test 4:

1. **Pattern 0xAA:** All **8 Green LEDs turn ON**, all 8 Red LEDs turn OFF (shows all slots vacant).
2. **Pattern 0x55:** All **8 Red LEDs turn ON**, all 8 Green LEDs turn OFF (shows all slots occupied).
3. **Pattern 0x00:** ALL **16 LEDs turn ON** together.
4. **Pattern 0xFF:** ALL **16 LEDs turn OFF** together.
5. **Individual Walk:** Each of the 16 LEDs turns ON one by one for 0.5 seconds while printing its name in the Serial Monitor!

---

## 🧪 Test 5: Test Barrier Gate Servos (`t04_servo`) — PASSED! ✅

- **Goal:** Test smooth opening (0° ➔ 90°) and closing (90° ➔ 0°) of both barrier gate servos.
- **Status:** **PASSED** (Verified on hardware; defective motor identified for replacement).

---

## 🧪 Test 6: Full Standalone System Test (`parktrack360.ino`) 🚀

Now that every individual hardware component is tested and verified, we run the **complete standalone firmware**! This runs the full system: 8 ultrasonic sensors, 16 LEDs, 16×2 LCD, 2 servo barrier gates, and serial commands.

### 🔌 Extra Library to Install:
Make sure **WebSockets** by Markus Sattler is installed in Arduino IDE Library Manager (alongside `ESP32Servo`, `LiquidCrystal_I2C`, and `ArduinoJson`).

### 🚀 Uploading the Full Firmware:
1. Connect ESP32 to laptop via USB.
2. Open **Arduino IDE**.
3. Verify your Wi-Fi details in `firmware/parktrack360/secrets.h` (Laptop IP is already configured to `192.168.29.37`).
4. Go to **File** ➔ **Open** ➔ select `firmware/parktrack360/parktrack360.ino`.
5. Click **Upload** (`➔`).
6. Open **Serial Monitor** at **115200 baud**.

### 🎮 How to Test Using Serial Monitor:
1. Type `help` ➔ see the complete list of commands.
2. Type `scan` ➔ verifies all 3 I²C devices (`0x25`, `0x26`, `0x27`).
3. Type `calibrate` with all 8 parking slots empty:
   - LCD will show `CALIBRATING...` then `CALIBRATION OK`.
   - All 8 slot LEDs turn **GREEN**!
4. **Place a toy car in any slot (e.g., G1):**
   - That slot's LED switches to **RED** within 0.5s.
   - LCD updates: `Occ: 1  Free: 7`.
5. **Remove the toy car:**
   - LED switches back to **GREEN**.
   - LCD updates: `Occ: 0  Free: 8`.
6. Type `gate entry open`:
   - Entry gate smoothly sweeps open, waits 5s, then closes!
7. Type `status` anytime to view all real-time distances, baselines, and gate states.

---

## 📹 Test 7: Dual USB Webcams Alignment & Testing

Now that you have connected the 2 USB cameras:

### 1. Scan Connected Webcams
Open PowerShell in the project directory and run:
```powershell
python tools/test_camera.py --list
```
* Windows will probe DirectShow devices.
* Your laptop's built-in webcam is typically `Index 0`.
* Your two plugged-in USB webcams will be detected as `Index 1` (Entry) and `Index 2` (Exit) (or `0` and `1` on a desktop PC).

### 2. Verify and Adjust `server/config.yaml`
Confirm the indices match in [server/config.yaml](file:///c:/Users/Hades/Documents/Smart-Park-Track-360/server/config.yaml):
```yaml
camera:
  mode: "dual"
  entry:
    source: 1    # Index of Entry webcam
  exit:
    source: 2    # Index of Exit webcam
```

### 3. Open Dual Split-Screen Preview & Focus Alignment
Run:
```powershell
python tools/test_camera.py --dual
```
* A split window will open showing **[ENTRY LANE]** on the left (green HUD) and **[EXIT LANE]** on the right (cyan HUD).
* **Lens Alignment:** Aim the Entry webcam at the entry boom barrier and the Exit webcam at the exit barrier (20–30 cm distance).
* **Focus Check:** Place a toy car at each gate and twist the lens focus ring (if manual focus) until the number tag is razor-sharp.
* Press `q` to close the preview when satisfied.

---

## 🌐 Test 8: End-to-End Live Web Dashboard & Autonomous Billing

With the ESP32 flashed and the 2 webcams aligned, start the full autonomous system!

### 1. Start the Host Server
Run the batch file or terminal command:
```powershell
.\run_server.bat
```
*(Or run `python -m uvicorn server.app:app --host 0.0.0.0 --port 8000`)*

### 2. Open the Web Dashboard in Your Browser
* **User Live Parking View:** [http://localhost:8000](http://localhost:8000)
  * View live Total Slots (8), Available Slots, Occupied Slots, and interactive Ground (G1–G4) / First (F1–F4) floor slot maps.
* **Admin Operator Portal:** [http://localhost:8000/admin](http://localhost:8000/admin) (Log in with `admin` / `admin360`).
  * Live gate manual override buttons, ESP32 WebSocket link monitor, hardware calibration trigger, and audit event logs.
* **Autonomous Payment & Checkout:** [http://localhost:8000/payment](http://localhost:8000/payment)

### 3. End-to-End Live Workflow Validation:
1. **ESP32 Connection:** Notice the dashboard badge changes to **`ESP32: ONLINE`** with green heartbeat pulses.
2. **Autonomous Slot Update:** Place a car in slot G1 ➔ The web dashboard slot G1 immediately turns **RED (Occupied)**, physical LED turns RED, and 16x2 LCD shows `Free: 7`.
3. **Barrier Gate Actuation:** Click "Open Entry Gate" in the Admin portal ➔ The physical SG90 servo sweeps to 90°, stays open for 5 seconds, and closes smoothly.
4. **Autonomous Cashless Checkout:**
   * Navigate to [http://localhost:8000/payment](http://localhost:8000/payment).
   * Enter Vehicle #1.
   * View the dwell time and calculated fee (₹40 for 1st hour, +₹20/hr thereafter).
   * Click **"Pay & Open Exit Gate"** ➔ Instant settlement receipt generates, and the Exit boom barrier lifts automatically!
