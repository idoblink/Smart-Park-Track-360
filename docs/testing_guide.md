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

## 🧪 Test 4: Test 16 Slot LEDs (`t03_leds`)

**Goal:** Test all 16 slot LEDs (8 Green + 8 Red) using both PCF8574 expanders. No external 5V power adapter needed—runs on ESP32 3.3V power over USB!

---

### 💡 Understanding "Active-LOW" LED Wiring

The PCF8574 expander chip is designed to **sink current** (pull to Ground). That means:
- The LED's **Anode (long leg, +)** connects to **ESP32 3.3V**.
- The LED's **Cathode (short leg, -)** connects through a **220Ω resistor** to the **PCF8574 pin (P0..P7)**.
- When the code sends a **0 (LOW)** to a pin, current flows into the PCF8574 and the LED turns **ON**!
- When the code sends a **1 (HIGH)** to a pin, the pin turns **OFF**.

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

### 📍 Part 2: Detailed LED Connections (LED by LED)

---

#### 🟢 Ground Floor Slot LEDs (Connected to PCF8574 #2 at `0x26`)

1. **Slot G1 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P0** on Expander `0x26`.

2. **Slot G1 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P1** on Expander `0x26`.

3. **Slot G2 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P2** on Expander `0x26`.

4. **Slot G2 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P3** on Expander `0x26`.

5. **Slot G3 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P4** on Expander `0x26`.

6. **Slot G3 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P5** on Expander `0x26`.

7. **Slot G4 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P6** on Expander `0x26`.

8. **Slot G4 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P7** on Expander `0x26`.

---

#### 🔵 First Floor Slot LEDs (Connected to PCF8574 #3 at `0x25`)

1. **Slot F1 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P0** on Expander `0x25`.

2. **Slot F1 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P1** on Expander `0x25`.

3. **Slot F2 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P2** on Expander `0x25`.

4. **Slot F2 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P3** on Expander `0x25`.

5. **Slot F3 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P4** on Expander `0x25`.

6. **Slot F3 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P5** on Expander `0x25`.

7. **Slot F4 Green LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P6** on Expander `0x25`.

8. **Slot F4 Red LED:**
   - Connect **Anode (long leg, +)** to ESP32 **3.3V Rail**.
   - Connect **Cathode (short leg, -)** through a 220Ω resistor to **Pin P7** on Expander `0x25`.

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

## 🧪 Test 3: Test 8 Ultrasonic Sensors (`t02_hcsr04`)

*(Requires 5V 2A external adapter — run after obtaining adapter).*

---

## 🧪 Test 5: Test Barrier Gate Servos (`t04_servo`)

**Goal:** Test smooth opening (90°) and closing (0°) of entry & exit gates.

---

## 🧪 Test 6: Test Gate Status LEDs (`t05_gateleds`)

**Goal:** Verify entry & exit gate red/green indicator pairs.
