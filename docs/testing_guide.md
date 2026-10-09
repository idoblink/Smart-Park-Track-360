# Complete Beginner's Hardware Testing Guide for Smart Park Track 360 (16x2 LCD Version)

Welcome! This guide explains **step-by-step** how to test every hardware part of your parking model. You don't need any prior coding experience—just follow these instructions carefully!

---

## 🛠️ Step 0: Software Setup (Do This Once)

Before uploading any test code, you need to prepare your computer.

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

## 🛠️ Address Setup for 3x PCF8574 Modules

You have **3 PCF8574 modules** sharing the same I²C bus. You MUST set different addresses so they don't collide:

1. **PCF8574 #1 (16x2 LCD Backpack):**
   - Leave `A0 A1 A2` un-bridged (default). Address = **`0x27`**.
2. **PCF8574 #2 (Ground Floor Slot LEDs):**
   - Make a small solder blob across the **`A0`** pad. Address = **`0x26`**.
3. **PCF8574 #3 (First Floor Slot LEDs):**
   - Make a small solder blob across the **`A1`** pad. Address = **`0x25`**.

---

## 🧪 Test 1: Check ESP32 Module Type (`t06_psram`) — PASSED! ✅

**Goal:** Confirm ESP32 is WROOM module (0 bytes PSRAM).  
**Status:** **PASSED** (PSRAM Size: 0 bytes, WROOM module OK).

---

## 🧪 Test 2: Scan I²C Devices (`t01_i2c_scan`)

**Goal:** Detect all 3 I²C modules on the shared bus.

### Wiring Needed:
- **16x2 LCD VCC** ➔ ESP32 **3.3V**
- **16x2 LCD GND** ➔ Ground Bus
- **16x2 LCD SDA** ➔ ESP32 **GPIO21**
- **16x2 LCD SCL** ➔ ESP32 **GPIO22**
- **PCF8574 #2 & #3 VCC** ➔ ESP32 **3.3V**
- **PCF8574 #2 & #3 GND** ➔ Ground Bus
- **PCF8574 #2 & #3 SDA** ➔ ESP32 **GPIO21**
- **PCF8574 #2 & #3 SCL** ➔ ESP32 **GPIO22**

### Steps:
1. Open `firmware/tests/t01_i2c_scan/t01_i2c_scan.ino`.
2. Upload the code and open Serial Monitor (115200 baud).
3. Press **EN / RST** button on ESP32 once.

### Expected Output:
```text
=== ParkTrack 360 — I2C Scanner (16x2 LCD Version) ===

Scanning I2C bus (SDA=21, SCL=22) ...

  Found device at 0x25  <-- PCF8574 (First Floor LEDs)
  Found device at 0x26  <-- PCF8574 (Ground Floor LEDs)
  Found device at 0x27  <-- PCF8574 (16x2 LCD Backpack)

Scan complete. Found 3 device(s).

=== I2C scan complete ===
```

---

## 🧪 Test 3: Test 8 Slot Sensors (`t02_hcsr04`)

**Goal:** Make sure all 8 ultrasonic sensors measure distances accurately.

### Wiring Needed:
- **External 5V supply** powered ON.
- Common ground connected.
- TRIG & ECHO connected per pin map:
  - **G1:** TRIG 13, ECHO 34
  - **G2:** TRIG 14, ECHO 35
  - **G3:** TRIG 27, ECHO 36
  - **G4:** TRIG 26, ECHO 39
  - **F1:** TRIG 25, ECHO 18
  - **F2:** TRIG 33, ECHO 5
  - **F3:** TRIG 32, ECHO 17
  - **F4:** TRIG 19, ECHO 16
- **Remember:** Every ECHO wire MUST use the **1kΩ / 2kΩ voltage divider** before going to the ESP32 pin!

### Steps:
1. Open `firmware/tests/t02_hcsr04/t02_hcsr04.ino`.
2. Upload and view Serial Monitor (115200 baud).

---

## 🧪 Test 4: Test 16 Slot LEDs (`t03_leds`)

**Goal:** Verify green/red slot LEDs light up.

### Wiring Needed:
- PCF8574 #2 (`0x26`) for Ground Floor (G1-G4).
- PCF8574 #3 (`0x25`) for First Floor (F1-F4).
- LEDs wired from PCF8574 pins (P0..P7) through 220Ω resistors to 3.3V (Active-LOW).

### Steps:
1. Open `firmware/tests/t03_leds/t03_leds.ino`.
2. Upload and observe LED patterns (0xAA green, 0x55 red, 0x00 all on, 0xFF all off, single walk).

---

## 🧪 Test 5: Test Barrier Gate Servos (`t04_servo`)

**Goal:** Test smooth opening (90°) and closing (0°) of entry & exit gates.

### Wiring Needed:
- **Entry Servo Signal** ➔ ESP32 **GPIO23**
- **Exit Servo Signal** ➔ ESP32 **GPIO15**
- **Servo VCC** ➔ **External 5V rail**
- **Servo GND** ➔ **Ground bus**
- Install a 470–1000 µF capacitor across the 5V rail near servos.

---

## 🧪 Test 6: Test Gate Status LEDs (`t05_gateleds`)

**Goal:** Verify entry & exit gate red/green indicator pairs.

### Wiring Needed:
- **Entry Pair** ➔ ESP32 **GPIO4**
- **Exit Pair** ➔ ESP32 **GPIO2**
