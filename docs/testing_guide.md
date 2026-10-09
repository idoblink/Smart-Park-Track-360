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

### Actual Verified Output:
```text
=== ParkTrack 360 — I2C Scanner (16x2 LCD Version) ===

Scanning I2C bus (SDA=21, SCL=22) ...

  Found device at 0x25  <-- PCF8574 (A1 bridged / First Floor LEDs)
  Found device at 0x26  <-- PCF8574 (A0 bridged / Ground Floor LEDs)
  Found device at 0x27  <-- PCF8574 (Default address / 16x2 LCD Backpack)

Scan complete. Found 3 device(s).

=== I2C scan complete ===
```

> 💡 **Troubleshooting Tip:** If scanner ever prints 126 devices (addresses 0x01..0x7E), check the **GND wire** on your breadboard—missing GND pulls SDA low!

---

## 🧪 Test 3: Test 8 Ultrasonic Sensors (`t02_hcsr04`)

**Goal:** Verify that all 8 HC-SR04 ultrasonic sensors accurately detect distances in centimeters.

---

### 1. Understanding the HC-SR04 Sensor Pins

Each HC-SR04 sensor has 4 pins on the front:
- **VCC:** Power (5V)
- **GND:** Ground (0V)
- **TRIG:** Trigger input (ESP32 tells sensor to shoot ultrasound pulse)
- **ECHO:** Echo output (Sensor tells ESP32 how long ultrasound took to bounce back)

---

### 2. ⚠️ CRITICAL: The 1kΩ / 2kΩ Voltage Divider on Every ECHO Wire

> **Why do we need this?**  
> The HC-SR04 sensor sends out a 5V signal on its ECHO pin. However, ESP32 GPIO pins are rated for **3.3V max**! Connecting a raw 5V ECHO pin directly to ESP32 can damage the pin.  
> The 2 resistors scale down 5V to a safe **3.33V**.

#### How to build 1 Voltage Divider on your breadboard (repeat for each sensor):

```text
HC-SR04 ECHO Pin ────[ 1kΩ Resistor ]──── • ────[ 2kΩ Resistor ]──── Ground Rail
                                          │
                                   Connect to ESP32 GPIO
```

- **Resistor 1 (1 kΩ / 1000 ohms):** Connect one side to HC-SR04 ECHO, connect the other side to a middle breadboard row.
- **Resistor 2 (2 kΩ / 2000 ohms):** Connect one side to that same middle breadboard row, connect the other side to Ground Rail.
- **Jumper Wire to ESP32:** Plug into that **same middle breadboard row** (the junction between the two resistors) and connect to the ESP32 ECHO pin!

*(Note: TRIG wire connects directly from ESP32 GPIO to the sensor's TRIG pin with NO resistors).*

---

### 3. Pin-by-Pin Wiring Table for All 8 Sensors

#### Power & Ground (All 8 sensors share this):
- **All VCC pins** ➔ Connect to **External 5V Power Rail** *(not ESP32 3.3V!)*
- **All GND pins** ➔ Connect to **Common Ground Rail**

#### Signal Wires:

| Slot | Floor | TRIG Pin ➔ ESP32 GPIO | ECHO Pin ➔ Divider Junction ➔ ESP32 GPIO | Notes |
|:---:|:---:|:---:|:---:|:---|
| **G1** | Ground | **GPIO 13** | **GPIO 34** | |
| **G2** | Ground | **GPIO 14** | **GPIO 35** | |
| **G3** | Ground | **GPIO 27** | **GPIO 36** | On board silkscreen labeled **VP** |
| **G4** | Ground | **GPIO 26** | **GPIO 39** | On board silkscreen labeled **VN** |
| **F1** | 1st Floor | **GPIO 25** | **GPIO 18** | |
| **F2** | 1st Floor | **GPIO 33** | **GPIO 5** | |
| **F3** | 1st Floor | **GPIO 32** | **GPIO 17** | On board silkscreen labeled **TX2** |
| **F4** | 1st Floor | **GPIO 19** | **GPIO 16** | On board silkscreen labeled **RX2** |

---

### 4. Step-by-Step Instructions to Run Test 3

1. **Power up your External 5V Power Adapter** (make sure ESP32 and 5V supply share the same Ground wire).
2. Open **Arduino IDE**.
3. Go to **File** ➔ **Open** ➔ navigate to `firmware/tests/t02_hcsr04/t02_hcsr04.ino`.
4. Click **Upload** (`➔`).
5. Open **Serial Monitor** (115200 baud).
6. Press **EN / RST** button on ESP32 once.

---

### 5. Expected Output & Physical Check

You will see live distance readings updating every ~500ms:

```text
=== ParkTrack 360 — HC-SR04 Sensor Test ===

G1:  12.3 cm | G2:  12.1 cm | G3:  12.5 cm | G4:  12.2 cm
F1:  12.4 cm | F2:  12.3 cm | F3:  12.6 cm | F4:  12.1 cm
---
```

#### 🖐️ Physical Check:
- Wave your hand ~5 cm above **Sensor G1** ➔ Watch `G1` reading drop to `~5.0 cm` on screen!
- Repeat for sensors G2, G3, G4, F1, F2, F3, F4 one by one.

---

### 🔍 Troubleshooting (`timeout`):
- **If a sensor reads `timeout`:**  
  1. Check if external 5V power is plugged in.
  2. Check if the 1kΩ/2kΩ resistor junction wire is plugged into the correct ESP32 ECHO pin.
  3. Verify TRIG wire is connected directly to its assigned GPIO.

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
