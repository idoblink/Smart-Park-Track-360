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

### Power Rail Smoothing Capacitor
* Electrolytic Capacitor (470µF to 1000µF) Positive leg (longer leg, +) ➔ Breadboard **5V Power Rail**
* Electrolytic Capacitor Negative leg (shorter leg with stripe, -) ➔ Breadboard **Common Ground Bus (GND)**

---

## 2. Shared I2C Bus Wiring (SDA & SCL)

### ESP32 I2C Pins
* **GPIO 21 (SDA)** ➔ Connects to all three I2C module SDA pins
* **GPIO 22 (SCL)** ➔ Connects to all three I2C module SCL pins

### 16x2 Character LCD Backpack (Address 0x27)
* Hardware setup: All address pads A0, A1, A2 remain unbridged (factory default)
* **VCC Pin** ➔ Breadboard **3.3V Logic Rail**
* **GND Pin** ➔ Breadboard **Common Ground Bus (GND)**
* **SDA Pin** ➔ ESP32 **GPIO 21**
* **SCL Pin** ➔ ESP32 **GPIO 22**

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
* **G1 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G1 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G1 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P0**
* **G1 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G1 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G1 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P1**

### Slot G2 LEDs
* **G2 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G2 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G2 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P2**
* **G2 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G2 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G2 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P3**

### Slot G3 LEDs
* **G3 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G3 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G3 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P4**
* **G3 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G3 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G3 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P5**

### Slot G4 LEDs
* **G4 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G4 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G4 Green LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P6**
* **G4 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **G4 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **G4 Red LED Resistor Leg 2** ➔ PCF8574 (0x26) **Pin P7**

---

## 4. First Floor Slot LEDs (PCF8574 at 0x25)

### Slot F1 LEDs
* **F1 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F1 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F1 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P0**
* **F1 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F1 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F1 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P1**

### Slot F2 LEDs
* **F2 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F2 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F2 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P2**
* **F2 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F2 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F2 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P3**

### Slot F3 LEDs
* **F3 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F3 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F3 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P4**
* **F3 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F3 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F3 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P5**

### Slot F4 LEDs
* **F4 Green LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F4 Green LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F4 Green LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P6**
* **F4 Red LED Anode (Long leg, +)** ➔ Breadboard **3.3V Logic Rail**
* **F4 Red LED Cathode (Short leg, -)** ➔ Leg 1 of 220Ω Resistor
* **F4 Red LED Resistor Leg 2** ➔ PCF8574 (0x25) **Pin P7**

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

### Single Overhead USB Webcam (Entry & Exit Lane Vision)
* **USB-A Connector** ➔ Laptop / Host PC USB Port (Direct connection, provides 5V power and MJPEG video feed)
* **Mounting Position** ➔ 25 cm to 35 cm overhead, centered between Entry and Exit lanes
* **Lens Alignment** ➔ Looking straight down at car roofs (tags 1–8 clearly visible in both lane ROIs)
* **Note** ➔ Camera does NOT connect to ESP32 (all computer vision runs on host laptop CPU)

---

## 9. Unconnected / Free Pins Note

### ESP32 Unconnected Pins
* **GPIO 4** ➔ Free / Unconnected (Gate indicator LEDs removed)
* **GPIO 2** ➔ Free / Unconnected (Gate indicator LEDs removed)
* **GPIO 12** ➔ Free / Unconnected (Boot strapping pin)
* **GPIO 0** ➔ Not broken out on 30-pin board
* **GPIO 1 (TX0)** ➔ Free / Reserved for USB Serial communication
* **GPIO 3 (RX0)** ➔ Free / Reserved for USB Serial communication

