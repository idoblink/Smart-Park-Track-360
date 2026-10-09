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

### ⚡ Power Rails Assignment (Breadboard Side Strips)
- **Red (+) Rail:** External 5V Power Supply Positive (+). Powers all 8 sensors VCC.
- **Blue (-) Rail:** Common Ground (GND). Connected to External 5V Adapter (-), all 8 sensors GND, AND ESP32 GND pin!

---

### 📍 Sensor 1: Ground Floor Slot 1 (G1)
1. **VCC:** Wire from Sensor G1 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor G1 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor G1 TRIG ➔ **ESP32 GPIO 13**
4. **Voltage Divider (Row 1):**
   - Plug 1kΩ resistor leg 1 into Sensor G1 ECHO wire, leg 2 into **Breadboard Row 1**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 1**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 1** ➔ **ESP32 GPIO 34**.

---

### 📍 Sensor 2: Ground Floor Slot 2 (G2)
1. **VCC:** Wire from Sensor G2 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor G2 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor G2 TRIG ➔ **ESP32 GPIO 14**
4. **Voltage Divider (Row 3):**
   - Plug 1kΩ resistor leg 1 into Sensor G2 ECHO wire, leg 2 into **Breadboard Row 3**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 3**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 3** ➔ **ESP32 GPIO 35**.

---

### 📍 Sensor 3: Ground Floor Slot 3 (G3)
1. **VCC:** Wire from Sensor G3 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor G3 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor G3 TRIG ➔ **ESP32 GPIO 27**
4. **Voltage Divider (Row 5):**
   - Plug 1kΩ resistor leg 1 into Sensor G3 ECHO wire, leg 2 into **Breadboard Row 5**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 5**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 5** ➔ **ESP32 GPIO 36** *(silkscreen **VP**)*.

---

### 📍 Sensor 4: Ground Floor Slot 4 (G4)
1. **VCC:** Wire from Sensor G4 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor G4 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor G4 TRIG ➔ **ESP32 GPIO 26**
4. **Voltage Divider (Row 7):**
   - Plug 1kΩ resistor leg 1 into Sensor G4 ECHO wire, leg 2 into **Breadboard Row 7**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 7**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 7** ➔ **ESP32 GPIO 39** *(silkscreen **VN**)*.

---

### 📍 Sensor 5: First Floor Slot 1 (F1)
1. **VCC:** Wire from Sensor F1 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor F1 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor F1 TRIG ➔ **ESP32 GPIO 25**
4. **Voltage Divider (Row 9):**
   - Plug 1kΩ resistor leg 1 into Sensor F1 ECHO wire, leg 2 into **Breadboard Row 9**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 9**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 9** ➔ **ESP32 GPIO 18**.

---

### 📍 Sensor 6: First Floor Slot 2 (F2)
1. **VCC:** Wire from Sensor F2 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor F2 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor F2 TRIG ➔ **ESP32 GPIO 33**
4. **Voltage Divider (Row 11):**
   - Plug 1kΩ resistor leg 1 into Sensor F2 ECHO wire, leg 2 into **Breadboard Row 11**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 11**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 11** ➔ **ESP32 GPIO 5**.

---

### 📍 Sensor 7: First Floor Slot 3 (F3)
1. **VCC:** Wire from Sensor F3 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor F3 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor F3 TRIG ➔ **ESP32 GPIO 32**
4. **Voltage Divider (Row 13):**
   - Plug 1kΩ resistor leg 1 into Sensor F3 ECHO wire, leg 2 into **Breadboard Row 13**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 13**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 13** ➔ **ESP32 GPIO 17** *(silkscreen **TX2**)*.

---

### 📍 Sensor 8: First Floor Slot 4 (F4)
1. **VCC:** Wire from Sensor F4 VCC ➔ **Red (+) 5V Rail**
2. **GND:** Wire from Sensor F4 GND ➔ **Blue (-) Ground Rail**
3. **TRIG:** Wire from Sensor F4 TRIG ➔ **ESP32 GPIO 19**
4. **Voltage Divider (Row 15):**
   - Plug 1kΩ resistor leg 1 into Sensor F4 ECHO wire, leg 2 into **Breadboard Row 15**.
   - Plug 2kΩ resistor leg 1 into **Breadboard Row 15**, leg 2 into **Blue (-) Ground Rail**.
   - Plug jumper wire from **Breadboard Row 15** ➔ **ESP32 GPIO 16** *(silkscreen **RX2**)*.

---

### 🚀 Step-by-Step Instructions to Run Test 3

1. Power ON your **External 5V Power Adapter**.
2. Open **Arduino IDE**.
3. Go to **File** ➔ **Open** ➔ navigate to `firmware/tests/t02_hcsr04/t02_hcsr04.ino`.
4. Click **Upload** (`➔`).
5. Open **Serial Monitor** (115200 baud).
6. Press **EN / RST** button on ESP32 once.

---

## 🧪 Test 4: Test 16 Slot LEDs (`t03_leds`)

**Goal:** Test all 16 slot LEDs (8 Green + 8 Red) using both PCF8574 expanders. No external 5V power adapter needed—runs on ESP32 3.3V power over USB!

---

### 💡 Understanding "Active-LOW" LED Wiring
- **Anode (long leg, +)** connects to **ESP32 3.3V**.
- **Cathode (short leg, -)** connects through a **220Ω resistor** to the **PCF8574 pin (P0..P7)**.
- Code sends **0 (LOW)** ➔ LED turns **ON**. Code sends **1 (HIGH)** ➔ LED turns **OFF**.

---

### 🔌 Part 1: Power & I²C Connections for the 2 LED Expanders

1. **Ground Floor Expander (PCF8574 #2, Address `0x26` — A0 bridged):**
   - **VCC** ➔ ESP32 **3.3V Rail** | **GND** ➔ ESP32 **GND Rail**
   - **SDA** ➔ ESP32 **GPIO 21** | **SCL** ➔ ESP32 **GPIO 22**

2. **First Floor Expander (PCF8574 #3, Address `0x25` — A1 bridged):**
   - **VCC** ➔ ESP32 **3.3V Rail** | **GND** ➔ ESP32 **GND Rail**
   - **SDA** ➔ ESP32 **GPIO 21** | **SCL** ➔ ESP32 **GPIO 22**

---

### 📍 Part 2: Detailed LED Connections (LED by LED)

#### 🟢 Ground Floor Slot LEDs (PCF8574 #2 at `0x26`)
- G1: Green ➔ P0, Red ➔ P1
- G2: Green ➔ P2, Red ➔ P3
- G3: Green ➔ P4, Red ➔ P5
- G4: Green ➔ P6, Red ➔ P7

#### 🔵 First Floor Slot LEDs (PCF8574 #3 at `0x25`)
- F1: Green ➔ P0, Red ➔ P1
- F2: Green ➔ P2, Red ➔ P3
- F3: Green ➔ P4, Red ➔ P5
- F4: Green ➔ P6, Red ➔ P7

---

## 🧪 Test 5: Test Barrier Gate Servos (`t04_servo`)

**Goal:** Test smooth opening (0° ➔ 90°) and closing (90° ➔ 0°) of both barrier gate servos.

---

### 🔌 Part 1: Power & Ground Setup
- **Servo VCC (Red Wire):** Connect both servo red wires to your **External 5V Power Rail**.
- **Servo GND (Black or Brown Wire):** Connect both servo black/brown wires to the **Common Ground Rail**.

---

### 📍 Part 2: Servo Signal Connections
1. **Entry Gate Servo Signal (Yellow/Orange Wire):** Connect to **ESP32 GPIO 23**.
2. **Exit Gate Servo Signal (Yellow/Orange Wire):** Connect to **ESP32 GPIO 15**.

---

## 🧪 Test 6: Test Gate Status LEDs (`t05_gateleds`)

**Goal:** Test the complementary Red/Green indicator LED pairs for Entry and Exit gates. **Runs directly from ESP32 USB power!**

---

### 📍 Wiring Instructions:

#### **Entry Gate Pair (Controlled by GPIO 4):**
1. **Entry Green LED:** Anode (+) ➔ 220Ω ➔ **ESP32 GPIO 4** | Cathode (-) ➔ **Ground Rail**.
2. **Entry Red LED:** Anode (+) ➔ 220Ω ➔ **ESP32 3.3V Rail** | Cathode (-) ➔ **ESP32 GPIO 4**.

#### **Exit Gate Pair (Controlled by GPIO 2):**
1. **Exit Green LED:** Anode (+) ➔ 220Ω ➔ **ESP32 GPIO 2** | Cathode (-) ➔ **Ground Rail**.
2. **Exit Red LED:** Anode (+) ➔ 220Ω ➔ **ESP32 3.3V Rail** | Cathode (-) ➔ **ESP32 GPIO 2**.
