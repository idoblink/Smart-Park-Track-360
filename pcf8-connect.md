# PCF8574 (HW-61) LED Expander Wiring Guide

This document details the exact pinout and wiring for the two **PCF8574 (HW-61 I2C Backpack)** modules used to drive the status LEDs for Ground Floor and First Floor parking slots in ParkTrack 360.

---

## 1. 4-Pin Main Header (ESP32 & Power Bus)

Both PCF8574 modules connect in parallel to the shared I2C bus and breadboard power rails:

| Module Pin | Target Connection | Notes |
| :--- | :--- | :--- |
| **GND** | Breadboard **Common Ground Bus (GND)** | Common ground shared with ESP32 |
| **VCC** | Breadboard **5V Power Rail** | Powered by 5V rail |
| **SDA** | ESP32 **GPIO 21** | Shared I2C data line |
| **SCL** | ESP32 **GPIO 22** | Shared I2C clock line |

> **Note:** The only signals running between the ESP32 and the PCF8574 modules are **SDA (GPIO 21)** and **SCL (GPIO 22)** plus the common ground reference.

---

## 2. LED Circuit Topology (Active-LOW Current Sinking)

The PCF8574 uses open-drain/quasi-bidirectional outputs that sink current to GND when commanded LOW (0):

1. **LED Anode (Long leg, +):** Connects directly to Breadboard **+5V Power Rail**.
2. **LED Cathode (Short leg, -):** Connects to Leg 1 of a **220Ω current-limiting resistor**.
3. **Resistor Leg 2:** Plugs into the specific PCF8574 pin indicated in the tables below.

---

## 3. Ground Floor Expander Wiring (Address 0x26 — A0 Solder Bridge Closed)

### 16-Pin Header Pinout:

| Header Pin # | PCB Label / Internal Pin | Connection / Target LED | Function & Wiring Notes |
| :---: | :---: | :--- | :--- |
| **Pin 1** | VSS (GND) | *Leave Disconnected* | Hardwired to GND on PCB (do NOT connect LEDs here) |
| **Pin 2** | VDD (+5V) | *Leave Disconnected* | Hardwired to 5V rail |
| **Pin 3** | V0 | *Leave Disconnected* | Contrast voltage divider output |
| **Pin 4** | **RS** (P0) | ➔ **Slot G1 Green LED** Resistor | Driven LOW when Slot G1 is VACANT |
| **Pin 5** | **RW** (P1) | ➔ **Slot G1 Red LED** Resistor | Driven LOW when Slot G1 is OCCUPIED |
| **Pin 6** | **E** (P2) | ➔ **Slot G2 Green LED** Resistor | Driven LOW when Slot G2 is VACANT |
| **Pin 7** | D0 | *DO NOT USE (Blank / NC)* | No internal trace on HW-61 PCB |
| **Pin 8** | D1 | *DO NOT USE (Blank / NC)* | No internal trace on HW-61 PCB |
| **Pin 9** | D2 | *DO NOT USE (Blank / NC)* | No internal trace on HW-61 PCB |
| **Pin 10** | D3 | *DO NOT USE (Blank / NC)* | No internal trace on HW-61 PCB |
| **Pin 11** | **D4** (P4) | ➔ **Slot G3 Green LED** Resistor | Driven LOW when Slot G3 is VACANT |
| **Pin 12** | **D5** (P5) | ➔ **Slot G3 Red LED** Resistor | Driven LOW when Slot G3 is OCCUPIED |
| **Pin 13** | **D6** (P6) | ➔ **Slot G4 Green LED** Resistor | Driven LOW when Slot G4 is VACANT |
| **Pin 14** | **D7** (P7) | ➔ **Slot G4 Red LED** Resistor | Driven LOW when Slot G4 is OCCUPIED |
| **Pins 15, 16** | Backlight | *Leave Disconnected* | Backlight power lines |
| **2-Pin Jumper** | **LED** Header (P3) | ➔ **Slot G2 Red LED** Resistor | Remove the black plastic shunt/jumper. Connect resistor to the pin switched by Q1 to GND. Driven LOW when Slot G2 is OCCUPIED. |

---

## 4. First Floor Expander Wiring (Address 0x25 — A1 Solder Bridge Closed)

### 16-Pin Header Pinout:

| Header Pin # | PCB Label / Internal Pin | Connection / Target LED | Function & Wiring Notes |
| :---: | :---: | :--- | :--- |
| **Pins 1 – 3** | VSS, VDD, V0 | *Leave Disconnected* | PCB supply and contrast pins |
| **Pin 4** | **RS** (P0) | ➔ **Slot F1 Green LED** Resistor | Driven LOW when Slot F1 is VACANT |
| **Pin 5** | **RW** (P1) | ➔ **Slot F1 Red LED** Resistor | Driven LOW when Slot F1 is OCCUPIED |
| **Pin 6** | **E** (P2) | ➔ **Slot F2 Green LED** Resistor | Driven LOW when Slot F2 is VACANT |
| **Pins 7 – 10** | D0 – D3 | *DO NOT USE (Blank / NC)* | No internal traces on HW-61 PCB |
| **Pin 11** | **D4** (P4) | ➔ **Slot F3 Green LED** Resistor | Driven LOW when Slot F3 is VACANT |
| **Pin 12** | **D5** (P5) | ➔ **Slot F3 Red LED** Resistor | Driven LOW when Slot F3 is OCCUPIED |
| **Pin 13** | **D6** (P6) | ➔ **Slot F4 Green LED** Resistor | Driven LOW when Slot F4 is VACANT |
| **Pin 14** | **D7** (P7) | ➔ **Slot F4 Red LED** Resistor | Driven LOW when Slot F4 is OCCUPIED |
| **Pins 15, 16** | Backlight | *Leave Disconnected* | Backlight power lines |
| **2-Pin Jumper** | **LED** Header (P3) | ➔ **Slot F2 Red LED** Resistor | Remove the black plastic shunt/jumper. Connect resistor to the switched pin. Driven LOW when Slot F2 is OCCUPIED. |

---

## 5. Critical Wiring Rules & Common Pitfalls

1. **Do NOT wire LEDs into Pins 1 to 3:**
   - Pin 1 is hardwired directly to GND on the PCB board. Plugging an LED here will make it stay permanently ON.
   - Pin 2 is hardwired directly to VCC (+5V). Plugging an LED here will keep it permanently OFF.
2. **Do NOT wire LEDs into Pins 7, 8, 9, 10:**
   - The HW-61 backpack operates the LCD in 4-bit mode (`D4` to `D7`). Pins 7 through 10 (`D0` to `D3`) are completely disconnected/unrouted traces on the board. Jump directly from **Pin 6 to Pin 11**.
3. **P3 Output Pin (Slot 2 Red):**
   - The PCF8574 bit 3 (`P3`) is routed to the base of an on-board transistor that controls the 2-pin header labeled **LED** (normally used for the LCD backlight jumper). Remove the black jumper block to connect Slot 2 Red LED.
