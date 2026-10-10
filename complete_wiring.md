# ParkTrack 360 — Complete Integration Wiring Guide

---

## 1. Power Supply and Ground Rails

### External 5V (2A) Power Supply
* Positive (+5V) output ➔ Breadboard **5V Power Rail**
* Negative (GND / 0V) output ➔ Breadboard **Common Ground Bus (GND)**

### ESP32 DevKit V1 Board
* Micro-USB port ➔ Laptop / PC USB port (Powers the ESP32 chip and provides Serial communication)
* **3V3 Pin** ➔ Breadboard **3.3V Logic Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**


---

## 2. Shared I2C Bus Wiring (SDA & SCL)

### ESP32 I2C Pins
* **GPIO 21 (SDA)** ➔ Connects to all three I2C module SDA pins
* **GPIO 22 (SCL)** ➔ Connects to all three I2C module SCL pins

### 16x2 Character LCD Backpack (Address 0x27)
* Hardware setup: All address pads A0, A1, A2 remain unbridged (factory default)
* **VCC Pin** ➔ Breadboard **5V Power Rail** (HD44780 liquid crystal matrix requires 5V for text contrast; 3.3V powers the backlight but leaves text blank)
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **SDA Pin** ➔ ESP32 **GPIO 21**
* **SCL Pin** ➔ ESP32 **GPIO 22**
* **Contrast Trimpot** ➔ Adjust the small blue potentiometer on the back of the LCD with a screwdriver until text is sharp!

### PCF8574 Module #2 — Ground Floor Slot LEDs (Address 0x26)
* Hardware setup: Solder bridge closed on **A0** pad only (A1 and A2 open)
* **VCC Pin** ➔ Breadboard **3.3V Logic Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **SDA Pin** ➔ ESP32 **GPIO 21**
* **SCL Pin** ➔ ESP32 **GPIO 22**

### PCF8574 Module #3 — First Floor Slot LEDs (Address 0x25)
* Hardware setup: Solder bridge closed on **A1** pad only (A0 and A2 open)
* **VCC Pin** ➔ Breadboard **3.3V Logic Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **SDA Pin** ➔ ESP32 **GPIO 21**
* **SCL Pin** ➔ ESP32 **GPIO 22**

---

## 3. Ground Floor Slot LEDs (PCF8574 at 0x26)

### Slot G1 LEDs
* **G1 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G1 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G1 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Header Pin 4 (RS / P0)**
* **G1 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G1 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G1 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **Header Pin 5 (RW / P1)**

### Slot G2 LEDs
* **G2 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G2 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G2 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Header Pin 6 (E / P2)**
* **G2 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G2 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G2 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **2-Pin LED Header (P3 / Transistor Pin)**

### Slot G3 LEDs
* **G3 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G3 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G3 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Header Pin 11 (D4 / P4)**
* **G3 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G3 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G3 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **Header Pin 12 (D5 / P5)**

### Slot G4 LEDs
* **G4 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G4 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G4 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Header Pin 13 (D6 / P6)**
* **G4 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **G4 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G4 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **Header Pin 14 (D7 / P7)**

---

## 4. First Floor Slot LEDs (PCF8574 at 0x25)

### Slot F1 LEDs
* **F1 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F1 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F1 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Header Pin 4 (RS / P0)**
* **F1 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F1 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F1 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **Header Pin 5 (RW / P1)**

### Slot F2 LEDs
* **F2 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F2 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F2 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Header Pin 6 (E / P2)**
* **F2 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F2 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F2 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **2-Pin LED Header (P3 / Transistor Pin)**

### Slot F3 LEDs
* **F3 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F3 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F3 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Header Pin 11 (D4 / P4)**
* **F3 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F3 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F3 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **Header Pin 12 (D5 / P5)**

### Slot F4 LEDs
* **F4 Green LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F4 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F4 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Header Pin 13 (D6 / P6)**
* **F4 Red LED Anode (Long leg, +)** ➔ Breadboard **5V Power Rail**
* **F4 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F4 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **Header Pin 14 (D7 / P7)**

---

## 5. Ground Floor Ultrasonic Sensors (HC-SR04)

### Sensor G1 (Ground Floor Slot 1)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 13**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 34**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

### Sensor G2 (Ground Floor Slot 2)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 14**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 35**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

### Sensor G3 (Ground Floor Slot 3)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 27**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 36 (silkscreened VP)**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

### Sensor G4 (Ground Floor Slot 4)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 26**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 39 (silkscreened VN)**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

---

## 6. First Floor Ultrasonic Sensors (HC-SR04)

### Sensor F1 (First Floor Slot 1)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 25**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 18**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

### Sensor F2 (First Floor Slot 2)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 33**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 5**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

### Sensor F3 (First Floor Slot 3)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 32**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 17 (silkscreened TX2)**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

### Sensor F4 (First Floor Slot 4)
* **VCC Pin** ➔ Breadboard **5V Power Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **TRIG Pin** ➔ ESP32 **GPIO 19**
* **ECHO Pin** ➔ Leg 1 of 1kΩ Resistor
* **1kΩ Resistor Leg 2** ➔ Breadboard Junction Row
* **Junction Row** ➔ ESP32 **GPIO 16 (silkscreened RX2)**
* **Junction Row** ➔ Leg 1 of 2kΩ Resistor
* **2kΩ Resistor Leg 2** ➔ Breadboard **Common Ground Bus (GND)**

---

## 7. Barrier Gate Servo Motors

### Entry Barrier Gate Servo
* **Signal Wire (Orange or Yellow)** ➔ ESP32 **GPIO 23**
* **Power Wire (Red)** ➔ Breadboard **5V Power Rail**
* **Ground Wire (Brown or Black)** ➔ Breadboard **Common Ground Bus (GND)**

### Exit Barrier Gate Servo
* **Signal Wire (Orange or Yellow)** ➔ ESP32 **GPIO 15**
* **Power Wire (Red)** ➔ Breadboard **5V Power Rail**
* **Ground Wire (Brown or Black)** ➔ Breadboard **Common Ground Bus (GND)**

---

## 8. USB Camera & Host Computer Wiring
 
### Dual USB Webcams Setup (Entry & Exit Lanes — Recommended)
* **Entry Lane USB Webcam:**
  * **USB-A Connector** ➔ Laptop / Host PC USB Port 1 (Provides 5V power and MJPEG video feed)
  * **Mounting Position** ➔ 20 cm to 30 cm directly facing or overhead above the **Entry Boom Barrier**
  * **Config Mapping** ➔ `camera.entry.source` in `server/config.yaml` (typically Index `0` or `1`)
* **Exit Lane USB Webcam:**
  * **USB-A Connector** ➔ Laptop / Host PC USB Port 2 (Direct connection or via powered USB hub)
  * **Mounting Position** ➔ 20 cm to 30 cm directly facing or overhead above the **Exit Boom Barrier**
  * **Config Mapping** ➔ `camera.exit.source` in `server/config.yaml` (typically Index `1` or `2`)
* **Note** ➔ Neither webcam connects to the ESP32 (all video streams directly to the host PC/laptop CPU)

### Alternative: Single Overhead Camera / Phone Stream (Fallback)
* **USB-A / Wi-Fi** ➔ 1 camera mounted 35 cm centrally overhead covering both lanes with software ROIs

---

## 9. Unconnected / Free Pins Note

### ESP32 Unconnected Pins
* **GPIO 4** ➔ Free / Unconnected (Gate indicator LEDs removed)
* **GPIO 2** ➔ Free / Unconnected (Gate indicator LEDs removed)
* **GPIO 12** ➔ Free / Unconnected (Boot strapping pin)
* **GPIO 0** ➔ Not broken out on 30-pin board
* **GPIO 1 (TX0)** ➔ Free / Reserved for USB Serial communication
* **GPIO 3 (RX0)** ➔ Free / Reserved for USB Serial communication

