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

## 🧪 Test 5: Test Barrier Gate Servos (`t04_servo`)

**Goal:** Test smooth opening (0° ➔ 90°) and closing (90° ➔ 0°) of both barrier gate servos.

---

### 🔌 Part 1: Power & Ground Setup
- **Servo VCC (Red Wire):** Connect both servo red wires to your **External 5V Power Rail** *(NEVER power servos from ESP32 pins!)*.
- **Servo GND (Black or Brown Wire):** Connect both servo black/brown wires to the **Common Ground Rail**.
- **Smoothing Capacitor:** Connect a **470µF to 1000µF electrolytic capacitor** across the External 5V rail near the servos:
  - **Long leg (+):** Connect to **Red 5V Rail**.
  - **Short leg (- / stripe side):** Connect to **Blue Ground Rail**.

---

### 📍 Part 2: Servo Signal Connections

1. **Entry Gate Servo:**
   - **Signal (Yellow or Orange Wire):** Connect directly to **ESP32 GPIO 23**.
2. **Exit Gate Servo:**
   - **Signal (Yellow or Orange Wire):** Connect directly to **ESP32 GPIO 15**.

---

### 🚀 Part 3: Step-by-Step Instructions to Run Test 5

1. Connect ESP32 to laptop via USB.
2. Power ON your **External 5V Power Adapter**.
3. Open **Arduino IDE**.
4. Go to **File** ➔ **Open** ➔ navigate to `firmware/tests/t04_servo/t04_servo.ino`.
5. Click **Upload** (`➔`).
6. Open **Serial Monitor** (115200 baud).
7. Press **EN / RST** button on ESP32 once.

---

### 👁️ What to Watch During Test 5:

1. The **Entry Servo** will sweep smoothly from **0° (closed) to 90° (open)** in 2° steps, hold for 1 second, and sweep back to **0° (closed)**.
2. The **Exit Servo** will perform the exact same smooth sweep right after.

> ⚠️ **Troubleshooting:**  
> If the ESP32 reboots or freezes when a servo starts moving, your external 5V supply is inadequate or the capacitor is missing.

---

## 🧪 Test 6: Test Gate Status LEDs (`t05_gateleds`)

**Goal:** Test the complementary Red/Green indicator LED pairs for Entry and Exit gates. **Runs directly from ESP32 USB power—no external 5V adapter needed!**

---

### 💡 Understanding Complementary LED Pair Wiring
Each gate indicator uses **1 single GPIO pin to control 2 LEDs** (Green and Red):
- When the GPIO pin is **HIGH (3.3V)**: Green LED turns **ON**, Red LED turns **OFF** (Gate Open / Free).
- When the GPIO pin is **LOW (0V)**: Red LED turns **ON**, Green LED turns **OFF** (Gate Closed / Full).

---

### 📍 Part 1: Entry Gate LED Pair Connections (Controlled by GPIO 4)

1. **Entry Green LED:**
   - Connect **Anode (long leg, +)** to one end of a **220Ω resistor**.
   - Connect the other end of that resistor to **ESP32 GPIO 4**.
   - Connect **Cathode (short leg, -)** directly to the **Common Ground Rail**.

2. **Entry Red LED:**
   - Connect **Anode (long leg, +)** to one end of a **220Ω resistor**.
   - Connect the other end of that resistor to **ESP32 3.3V Rail**.
   - Connect **Cathode (short leg, -)** directly to **ESP32 GPIO 4**.

---

### 📍 Part 2: Exit Gate LED Pair Connections (Controlled by GPIO 2)

1. **Exit Green LED:**
   - Connect **Anode (long leg, +)** to one end of a **220Ω resistor**.
   - Connect the other end of that resistor to **ESP32 GPIO 2**.
   - Connect **Cathode (short leg, -)** directly to the **Common Ground Rail**.

2. **Exit Red LED:**
   - Connect **Anode (long leg, +)** to one end of a **220Ω resistor**.
   - Connect the other end of that resistor to **ESP32 3.3V Rail**.
   - Connect **Cathode (short leg, -)** directly to **ESP32 GPIO 2**.

---

### 🚀 Part 3: Step-by-Step Instructions to Run Test 6

1. Connect ESP32 to laptop via USB.
2. Open **Arduino IDE**.
3. Go to **File** ➔ **Open** ➔ navigate to `firmware/tests/t05_gateleds/t05_gateleds.ino`.
4. Click **Upload** (`➔`).
5. Open **Serial Monitor** (115200 baud).
6. Press **EN / RST** button on ESP32 once.

---

### 👁️ What to Watch During Test 6:

1. **Entry Gate:** Toggles Green ON (Red OFF) for 2 seconds ➔ then Red ON (Green OFF) for 2 seconds.
2. **Exit Gate:** Toggles Green ON (Red OFF) for 2 seconds ➔ then Red ON (Green OFF) for 2 seconds.
3. **Both:** Turn Green together ➔ then turn Red together!
