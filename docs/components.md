# ParkTrack 360 — Complete Component List & Hardware Specification

This document details every hardware component, electronic part, sensor, actuator, power requirement, and computer vision element used across the entire **Smart Park Track 360** project.

---

## 1. Microcontroller & Computing Units

* **ESP32 DevKit V1 (30-Pin Board)**
  * **Quantity:** 1
  * **Module Variant:** ESP32-WROOM-32 (0 bytes PSRAM verified via `t06_psram`)
  * **Processor:** Xtensa Dual-Core 32-bit LX6 running at 240 MHz
  * **Connectivity:** 2.4 GHz Wi-Fi (802.11 b/g/n) and Bluetooth 4.2 BLE
  * **Operating Voltage:** 3.3V Logic level
  * **Role:** Real-time edge controller. Manages 8 ultrasonic sensors, 16 slot LEDs via dual PCF8574 expanders, 16x2 LCD display, 2 barrier servos, and WebSocket communication with the laptop server.

* **Laptop / Host Computer**
  * **Quantity:** 1
  * **Operating System:** Windows 10/11 (or Linux/macOS)
  * **Role:** Runs the Python FastAPI server, SQLite database, web dashboard, and the CPU-optimized YOLO vision pipeline. Provides 2.4 GHz network host (Mobile Hotspot or shared router) and USB connection for camera and ESP32 programming.

* **USB Cable (Type-A to Micro-USB)**
  * **Quantity:** 1
  * **Role:** Connects ESP32 to Laptop for flashing firmware, USB Serial debugging (115200 baud), and logic power. Must be a high-quality data cable.

---

## 2. Computer Vision & Camera Hardware

### Research & Camera Selection

For recognizing small printed digit labels (1–8) on toy Hot Wheels cars, the camera must satisfy three key constraints:
1. **Short Focal Distance / Macro Focus (25 cm to 35 cm):** Standard off-the-shelf fixed-focus webcams are pre-focused at infinity (1 to 2 meters) and become blurry when placed 25 cm away. The chosen camera MUST either feature an adjustable manual focus ring or a macro-capable autofocus mechanism.
2. **Single Camera Multi-ROI Coverage:** A single camera mounted overhead covers both the entry and exit lanes simultaneously, streaming at 1280×720 (720p) or 1920×1080 (1080p) MJPEG over USB.
3. **Driver Compatibility:** Standard UVC (USB Video Class) driver support without proprietary bloatware, compatible with OpenCV `CAP_DSHOW` on Windows.

### Recommended Camera Models:

* **Option 1: Dual USB Webcams (Recommended Real-World / Physical Model Setup — ₹800 to ₹1,400 for pair)**
  * **Configuration:** 2 independent USB webcams plugged into your laptop / host PC (e.g., Quantum QHM495LM or Zebronics Crystal Clear).
  * **Placement:**
    * **Webcam 1 (Entry Lane):** Mounted directly at or above the Entry boom barrier (Camera Index `0` or `1`).
    * **Webcam 2 (Exit Lane):** Mounted directly at or above the Exit boom barrier (Camera Index `1` or `2`).
  * **Advantages over single camera:**
    * **Zero perspective distortion:** No need for an unwieldy high-mast tripod trying to split view between two separated lanes.
    * **Double the resolution:** Each lane gets a full 1280×720 or 1080p sensor feed dedicated to its barrier.
    * **Closer macro distance (20–30 cm):** High-confidence digit reading under standard ambient lighting.

* **Option 2: Android Smartphone Camera (Ideal for Rapid Zero-Cost Testing)**
  * **Key Feature:** Exceptional image sensor, tap-to-focus macro capability at 20–35 cm, high resolution (1080p/720p). Connects via Wi-Fi (using free "IP Webcam" app) or USB (via DroidCam / Iriun Webcam).
  * **Connection Type:** Wi-Fi MJPEG stream URL (e.g., `http://192.168.1.X:8080/video`) or Virtual DirectShow Webcam.
  * **Cost:** ₹0 (uses your existing Android phone).

* **Option 3: Single Overhead Webcam (Budget / Minimalist Setup)**
  * **Key Feature:** One central camera mounted high above both lanes using split software ROIs.
  * **Resolution:** 720p native sensor at 30 FPS.

### Mounting & Tag Accessories:
* **Overhead Camera Stand / Gooseneck Arm:** Rigid mount holding the webcam 25–35 cm vertically above the track lanes.
* **Toy Cars:** 8 Hot Wheels / Matchbox cars (numbered 1 through 8).
* **Printed Digit Tags:** Matte white sticker paper printed with bold digits (12 mm height, font DejaVu Sans Mono Bold). Matte finish avoids camera glare.

---

## 3. Sensors & Sensing Circuitry

* **HC-SR04 Ultrasonic Distance Sensors**
  * **Quantity:** 8 (G1, G2, G3, G4 on Ground floor; F1, F2, F3, F4 on First floor)
  * **Operating Voltage:** 5V DC (powered from external 5V rail)
  * **Trigger Input:** 3.3V compatible (driven directly from ESP32 GPIO)
  * **Echo Output:** 5V TTL pulse (must NOT connect directly to ESP32 pins)
  * **Role:** Detects physical car presence in each slot by measuring empty baseline vs. car roof height.

* **Voltage Divider Resistors for HC-SR04 Echo Lines**
  * **1 kΩ Resistors (1/4W, 5% or 1%):** Quantity: 8 (Top leg: sensor ECHO pin to divider junction)
  * **2 kΩ Resistors (1/4W, 5% or 1%):** Quantity: 8 (Bottom leg: divider junction to Common Ground)
  * **Function:** Steps down the 5V Echo pulse to safe 3.33V level (5V × 2k / (1k + 2k) = 3.33V) for ESP32 inputs.

---

## 4. Visual Indicators & Display

* **16×2 Character LCD Display (JHD 162A or compatible)**
  * **Quantity:** 1
  * **Display Layout:** 16 columns by 2 rows of alphanumeric characters with blue/green LED backlight.
  * **Role:** Driver-facing entrance display showing real-time occupancy (`Occ: N  Free: M`), system status, or `PARKING FULL`.

* **PCF8574 I²C LCD Backpack (HW-61 or standard backpack module)**
  * **Quantity:** 1 (soldered directly to rear of 16x2 LCD)
  * **I²C Address:** `0x27` (Address solder pads A0, A1, A2 remain unbridged)
  * **Operating Voltage:** 3.3V (VCC to 3.3V rail, GND to common ground)
  * **Role:** Converts the parallel 16-pin LCD interface into standard 2-wire I²C (SDA/SCL).

* **PCF8574 I²C 8-Bit I/O Expanders for Slot LEDs**
  * **Quantity:** 2 modules (Breakout boards with A0, A1, A2 address pads)
  * **Expander #2 (Ground Floor LEDs):** Address `0x26` (A0 pad bridged with solder blob)
  * **Expander #3 (First Floor LEDs):** Address `0x25` (A1 pad bridged with solder blob)
  * **Role:** Drives all 16 slot LEDs using active-LOW current-sinking logic, saving 16 GPIO pins on the ESP32.

* **5mm Green LEDs**
  * **Quantity:** 8 (one for each slot G1..G4 and F1..F4)
  * **Role:** Indicates slot is **VACANT** (Turned ON when slot distance matches empty baseline).

* **5mm Red LEDs**
  * **Quantity:** 8 (one for each slot G1..G4 and F1..F4)
  * **Role:** Indicates slot is **OCCUPIED** (Turned ON when car is parked in the slot).

* **220 Ω Current-Limiting Resistors for LEDs**
  * **Quantity:** 16
  * **Role:** Limits LED forward current to safe level (~7 mA at 3.3V) between LED cathode and PCF8574 sink pins.

---

## 5. Actuators & Mechanical Barrier Gates

* **Micro Servo Motors (SG90 or MG90S Class)**
  * **Quantity:** 2 (1× Entry Gate, 1× Exit Gate)
  * **Operating Voltage:** 5V DC (External power supply ONLY)
  * **Control Signal:** 50 Hz PWM from ESP32 (GPIO 23 for Entry, GPIO 15 for Exit)
  * **Pulse Width Range:** 500 µs (0°) to 2400 µs (90°)
  * **Role:** Opens and closes barrier arms for authorized vehicle entry and exit.

* **Barrier Gate Arms & Base Mounts**
  * **Quantity:** 2 arms
  * **Material:** Lightweight plastic horn arm, cardboard strip, or 3D printed arm.

---

## 6. Power Supply & Circuit Conditioning

* **External 5V DC Regulated Power Supply**
  * **Quantity:** 1
  * **Specification:** 5V DC, minimum 2.0 Amperes (2A) current rating.
  * **Role:** Dedicated power source for high-current loads (8 HC-SR04 sensors ~120 mA total, 2 servos pulling up to 1.3A stall peak). Prevents ESP32 brownout resets.

* **DC Barrel Jack to Screw Terminal Adapter (5.5mm × 2.1mm Female)**
  * **Quantity:** 1
  * **Role:** Connects the 5V power adapter plug safely to breadboard wire leads (+5V and GND).


---

## 7. Prototyping Hardware & Wiring

* **Full-Size Solderless Breadboards (830 Tie-Points)**
  * **Quantity:** 2 to 3
  * **Role:** Holds the ESP32, expanders, resistors, wiring buses, and sensor interface dividers.

* **Jumper Wires**
  * **Male-to-Male (M-M):** 40+ wires (for breadboard rail connections, resistors, jumpers)
  * **Male-to-Female (M-F):** 25+ wires (for connecting HC-SR04 sensors, LCD backpack, and servos to breadboard)

* **Physical 2-Floor Model Structure**
  * **Material:** Cardboard, MDF, foam core, or 3D printed frame
  * **Configuration:** Ground Floor (Slots G1–G4), Ramp, First Floor (Slots F1–F4), Entry Lane, Exit Lane.
