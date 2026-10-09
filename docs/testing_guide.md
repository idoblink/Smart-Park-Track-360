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

## 🧪 Test 3: Test 8 Ultrasonic Sensors (`t02_hcsr04`)

**Goal:** Verify that all 8 HC-SR04 ultrasonic sensors accurately detect distances in centimeters.

---

### ⚡ Part 1: Setting Up the Breadboard & External 5V Power Source

Before connecting any sensors, set up your breadboard power strips properly:

1. **Identify the Power Rails on your Breadboard:**
   - The strip with the **Red line (+)** will be your **5V Power Rail**.
   - The strip with the **Blue or Black line (-)** will be your **Common Ground Rail**.

2. **Connect the External 5V Power Adapter:**
   - Take the **Positive (+5V / Red wire)** coming from your External 5V adapter and plug it into the **Red (+) Rail** on your breadboard.
   - Take the **Negative (GND / Black wire)** coming from your External 5V adapter and plug it into the **Blue (-) Rail** on your breadboard.

3. **Connect the Shared Ground Wire:**
   - Plug a jumper wire from the **GND pin** of your ESP32 board directly into the **Blue (-) Rail** on your breadboard.

4. **Keep 3.3V and 5V Separate:**
   - Do **NOT** connect the ESP32 `3.3V` pin to the external 5V Red rail!

---

### 🔌 Part 2: How to Build the Voltage Divider for Each Sensor

Because the sensors output a 5V signal on their ECHO pin and the ESP32 can only take 3.3V, you must build a small "Voltage Divider" on the breadboard for each sensor using two resistors: **1kΩ** (1000 ohms) and **2kΩ** (2000 ohms).

Here is how to build one divider on the breadboard:

1. Pick an unused row on your breadboard (for example, **Row 10**).
2. Take a **1kΩ resistor**:
   - Plug one leg into the wire coming from the Sensor's **ECHO pin**.
   - Plug the other leg into **Row 10**.
3. Take a **2kΩ resistor**:
   - Plug one leg into **Row 10** (in the exact same row as the 1kΩ resistor leg).
   - Plug the other leg into the **Blue (-) Common Ground Rail**.
4. Take a jumper wire to connect to the ESP32:
   - Plug one end into **Row 10** (where the two resistors meet).
   - Plug the other end into the designated **ESP32 GPIO pin** for that sensor's ECHO.

---

### 📍 Part 3: Step-by-Step Sensor Connections (Sensor by Sensor)

#### 🟢 Sensor 1: Ground Floor Slot 1 (G1)
1. **VCC:** Connect jumper wire from **G1 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **G1 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **G1 Sensor TRIG pin** to **ESP32 GPIO 13**.
4. **ECHO:** Connect **G1 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 34**.

#### 🟢 Sensor 2: Ground Floor Slot 2 (G2)
1. **VCC:** Connect jumper wire from **G2 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **G2 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **G2 Sensor TRIG pin** to **ESP32 GPIO 14**.
4. **ECHO:** Connect **G2 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 35**.

#### 🟢 Sensor 3: Ground Floor Slot 3 (G3)
1. **VCC:** Connect jumper wire from **G3 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **G3 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **G3 Sensor TRIG pin** to **ESP32 GPIO 27**.
4. **ECHO:** Connect **G3 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 36** *(labeled **VP**)*.

#### 🟢 Sensor 4: Ground Floor Slot 4 (G4)
1. **VCC:** Connect jumper wire from **G4 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **G4 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **G4 Sensor TRIG pin** to **ESP32 GPIO 26**.
4. **ECHO:** Connect **G4 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 39** *(labeled **VN**)*.

#### 🔵 Sensor 5: First Floor Slot 1 (F1)
1. **VCC:** Connect jumper wire from **F1 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **F1 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **F1 Sensor TRIG pin** to **ESP32 GPIO 25**.
4. **ECHO:** Connect **F1 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 18**.

#### 🔵 Sensor 6: First Floor Slot 2 (F2)
1. **VCC:** Connect jumper wire from **F2 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **F2 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **F2 Sensor TRIG pin** to **ESP32 GPIO 33**.
4. **ECHO:** Connect **F2 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 5**.

#### 🔵 Sensor 7: First Floor Slot 3 (F3)
1. **VCC:** Connect jumper wire from **F3 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **F3 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **F3 Sensor TRIG pin** to **ESP32 GPIO 32**.
4. **ECHO:** Connect **F3 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 17** *(labeled **TX2**)*.

#### 🔵 Sensor 8: First Floor Slot 4 (F4)
1. **VCC:** Connect jumper wire from **F4 Sensor VCC pin** to **Red (+) External 5V Rail**.
2. **GND:** Connect jumper wire from **F4 Sensor GND pin** to **Blue (-) Common Ground Rail**.
3. **TRIG:** Connect jumper wire directly from **F4 Sensor TRIG pin** to **ESP32 GPIO 19**.
4. **ECHO:** Connect **F4 Sensor ECHO pin** through 1kΩ/2kΩ divider to **ESP32 GPIO 16** *(labeled **RX2**)*.

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
