# Complete Beginner's Hardware Testing Guide for Smart Park Track 360

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
6. On the left sidebar of Arduino IDE, click the **Boards Manager** icon (it looks like a small circuit board).
7. In the search bar, type `esp32`.
8. Find **esp32 by Espressif Systems** and click **Install**. Wait until the installation finishes.

### 3. Install Required Libraries
1. On the left sidebar of Arduino IDE, click the **Library Manager** icon (it looks like a stack of books).
2. In the search bar, type `ESP32Servo`.
3. Find **ESP32Servo by Kevin Harrington** and click **Install**.
4. (Optional) Search for `Adafruit SSD1306` and `ArduinoJson` and install them as well.

---

## ⚙️ How to Upload Code to ESP32

Whenever you test a sketch, follow these exact steps:

1. Connect your **ESP32 board to your computer** using a micro-USB cable.
2. In Arduino IDE, go to **Tools** ➔ **Board** ➔ **esp32** ➔ select **ESP32 Dev Module**.
3. Go to **Tools** ➔ **Port** ➔ select the COM port corresponding to your ESP32 (e.g., `COM3`, `COM4`, or `COM5`).
4. Click **File** ➔ **Open** ➔ navigate to the test file (e.g., `firmware/tests/t06_psram/t06_psram.ino`).
5. Click the **Upload** button (the green arrow `➔` icon at the top left).
6. Wait for the message at the bottom: `Done uploading`.
7. Click the **Serial Monitor** icon at the top right (it looks like a magnifying glass).
8. **CRITICAL:** Set the Baud Rate in the Serial Monitor to **115200** (bottom right dropdown of the monitor tab).

---

## 🧪 Test 1: Check ESP32 Module Type (`t06_psram`)

**Goal:** Confirm your ESP32 module is **WROOM** (which leaves GPIO16 and GPIO17 free for sensors).

### Wiring Needed:
- **NONE!** Just plug the ESP32 into your laptop via USB.

### Steps:
1. Open `firmware/tests/t06_psram/t06_psram.ino` in Arduino IDE.
2. Upload the code and open the Serial Monitor (115200 baud).

### Expected Output:
```text
=== ParkTrack 360 — PSRAM Check ===

PSRAM Size: 0 bytes

Result: WROOM module (OK -- GPIO16/17 are available)

=== PSRAM check complete ===
```

> ⚠️ **What if it says `WROVER module`?**  
> If `PSRAM Size` is greater than 0 (e.g. 4194304 bytes), stop and inform the agent. GPIO16/17 are occupied by internal memory on WROVER boards.

---

## 🧪 Test 2: Find I²C Devices (`t01_i2c_scan`)

**Goal:** Detect the I²C addresses for your OLED display and 2x PCF8574 expanders.

### Wiring Needed:
- **OLED VCC** ➔ ESP32 **3.3V**
- **OLED GND** ➔ Ground Bus
- **OLED SDA** ➔ ESP32 **GPIO21**
- **OLED SCL** ➔ ESP32 **GPIO22**
- **PCF8574 #1 & #2 VCC** ➔ ESP32 **3.3V**
- **PCF8574 #1 & #2 GND** ➔ Ground Bus
- **PCF8574 #1 & #2 SDA** ➔ ESP32 **GPIO21**
- **PCF8574 #1 & #2 SCL** ➔ ESP32 **GPIO22**

### Steps:
1. Open `firmware/tests/t01_i2c_scan/t01_i2c_scan.ino`.
2. Upload the code and open the Serial Monitor (115200 baud).

### Expected Output:
```text
=== ParkTrack 360 — I2C Scanner ===

Scanning I2C bus (SDA=21, SCL=22) ...

  Found device at 0x20  <-- PCF8574 (address offset 0)
  Found device at 0x21  <-- PCF8574 (address offset 1)
  Found device at 0x3C  <-- SSD1306 OLED

Scan complete. Found 3 device(s).

=== I2C scan complete ===
```

> 💡 **Troubleshooting:**
> - If `0` devices found: check if SDA/SCL wires are swapped, or if 3.3V/GND are loose.
> - If PCF8574 shows `0x38` and `0x39`: you have **PCF8574A** chips. That's fine! Just note it down.

---

## 🧪 Test 3: Test 8 Slot Sensors (`t02_hcsr04`)

**Goal:** Make sure all 8 ultrasonic sensors measure distances accurately.

### Wiring Needed:
- **External 5V supply** powered ON.
- Common ground connected.
- TRIG & ECHO connected according to the pin map:
  - **G1:** TRIG 13, ECHO 34
  - **G2:** TRIG 14, ECHO 35
  - **G3:** TRIG 27, ECHO 36
  - **G4:** TRIG 26, ECHO 39
  - **F1:** TRIG 25, ECHO 18
  - **F2:** TRIG 33, ECHO 5
  - **F3:** TRIG 32, ECHO 17
  - **F4:** TRIG 19, ECHO 16
- **Remember:** Every ECHO wire must use the **1kΩ / 2kΩ voltage divider** before going into the ESP32 pin!

### Steps:
1. Open `firmware/tests/t02_hcsr04/t02_hcsr04.ino`.
2. Upload the code and open the Serial Monitor (115200 baud).

### Expected Output:
```text
G1:  12.3 cm | G2:  12.1 cm | G3:  12.5 cm | G4:  12.2 cm
F1:  12.4 cm | F2:  12.3 cm | F3:  12.6 cm | F4:  12.1 cm
---
```

### Physical Check:
- Wave your hand or place a toy car ~5 cm above each sensor individually.
- Watch the distance value for that specific slot drop down to ~5 cm on the screen!
- If a sensor says `timeout`, re-check its 5V power, GND, TRIG, and ECHO wires.

---

## 🧪 Test 4: Test 16 Slot LEDs (`t03_leds`)

**Goal:** Verify that green/red slot LEDs light up in response to commands.

### Wiring Needed:
- PCF8574 expanders wired to I²C (SDA 21, SCL 22).
- LEDs wired from PCF8574 pins (P0..P7) through 220Ω resistors to 3.3V (Active-LOW: 0 = ON).

### Steps:
1. Open `firmware/tests/t03_leds/t03_leds.ino`.
2. Upload the code and open the Serial Monitor (115200 baud).

### Expected Output & Visual Check:
1. **Pattern 0xAA:** All **Green LEDs turn ON**, all Red LEDs turn OFF.
2. **Pattern 0x55:** All **Red LEDs turn ON**, all Green LEDs turn OFF.
3. **Pattern 0x00:** ALL 16 LEDs turn ON.
4. **Pattern 0xFF:** ALL 16 LEDs turn OFF.
5. **Individual Walk:** Each LED turns ON one by one for 0.5 seconds.

---

## 🧪 Test 5: Test Barrier Gate Servos (`t04_servo`)

**Goal:** Test smooth opening (90°) and closing (0°) of entry and exit gates.

### Wiring Needed:
- **Entry Servo Signal** ➔ ESP32 **GPIO23**
- **Exit Servo Signal** ➔ ESP32 **GPIO15**
- **Servo Power (Red wire)** ➔ **External 5V rail** (NEVER power servos from ESP32 pins!)
- **Servo Ground (Black/Brown wire)** ➔ **Ground bus**
- Install a 470–1000 µF capacitor across the 5V rail near the servos.

### Steps:
1. Open `firmware/tests/t04_servo/t04_servo.ino`.
2. Upload the code and open the Serial Monitor (115200 baud).

### Expected Behaviour:
- The **Entry Servo** sweeps smoothly from 0° to 90°, pauses for 1 second, then sweeps back to 0°.
- The **Exit Servo** performs the same sweep immediately after.

> ⚠️ **Did the ESP32 restart or freeze?**  
> This means your 5V power supply cannot supply enough current or the capacitor is missing. Make sure your 5V power adapter supports at least 2A.

---

## 🧪 Test 6: Test Gate Status LEDs (`t05_gateleds`)

**Goal:** Verify the complementary red/green indicator LEDs at the entry & exit gates.

### Wiring Needed:
- **Entry Pair** ➔ ESP32 **GPIO4**
- **Exit Pair** ➔ ESP32 **GPIO2**

### Steps:
1. Open `firmware/tests/t05_gateleds/t05_gateleds.ino`.
2. Upload the code and open the Serial Monitor (115200 baud).

### Expected Visual Check:
- Entry Gate: Green ON ➔ Red ON
- Exit Gate: Green ON ➔ Red ON
- Both Green ON ➔ Both Red ON (repeats every 2 seconds).

---

## 📝 What to Send Back to the AI Agent

Once you finish these tests, simply copy and paste the Serial Monitor outputs into [`docs/wiring.md`](file:///C:/Users/Hades/Documents/Smart-Park-Track-360/docs/wiring.md) and answer these simple questions:

1. **PSRAM check result:** Did `t06_psram` report `WROOM module (OK)`?
2. **I²C scan result:** What addresses were found in `t01_i2c_scan`? (e.g. 0x20, 0x21, 0x3C)
3. **OLED size:** Is your OLED screen 128x64 or 128x32?
4. **Sensors & Servos:** Did all 8 sensors measure distance and did both servos sweep smoothly?
