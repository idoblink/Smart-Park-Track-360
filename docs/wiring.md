# ParkTrack 360 — Wiring Verification Record

## Board

- **Module:** ESP32 DevKit V1 (30-pin)
- **Variant:** ☑ WROOM (OK) / ☐ WROVER (PROBLEM — notify owner)
- **PSRAM size from t06_psram:** 0 bytes (Confirmed - WROOM module)

## Display & I²C Configuration

- **Display type:** **16x2 Character LCD** (with PCF8574 I²C backpack `JHD 162A`)
- **Total PCF8574 Expanders on I²C bus:** 3 modules
- **Library:** `LiquidCrystal_I2C` by Frank de Brabander

### Required I²C Address Map & Solder Bridge Settings (HW-61 Modules)

To prevent address conflicts on the shared I²C bus (SDA = GPIO21, SCL = GPIO22), the 3 PCF8574 modules MUST have distinct addresses:

| Module | Purpose | Address | Solder Pad Bridge (HW-61) | Notes |
|--------|---------|---------|---------------------------|-------|
| **PCF8574 #1** | 16x2 LCD Display Backpack | `0x27` (or `0x3F`) | All open (default) | Do NOT solder pads on LCD backpack |
| **PCF8574 #2** | Ground Floor Slot LEDs (G1–G4) | `0x26` | Bridge **A0** pad with solder blob | Ground floor active-LOW expander |
| **PCF8574 #3** | First Floor Slot LEDs (F1–F4) | `0x25` | Bridge **A1** pad with solder blob | First floor active-LOW expander |

---

## Complete Wiring Guide (16x2 LCD Version)

### 1. Common Ground & Power Rails
- **Common Ground (GND Bus):** ESP32 GND, External 5V GND, 8x HC-SR04 GND, 3x PCF8574 GND, 2x Servo GND.
- **ESP32 3.3V Rail:** Powers the 16x2 LCD backpack VCC and the 2x Slot LED PCF8574 module VCCs.
- **External 5V 2A Rail:** Powers 8x HC-SR04 VCC and 2x Servo VCC.

### 2. I²C Shared Bus (3.3V Logic)
All 3 I²C modules share the same SDA & SCL lines:
- **ESP32 GPIO21** ➔ SDA (16x2 LCD SDA, PCF8574 #2 SDA, PCF8574 #3 SDA)
- **ESP32 GPIO22** ➔ SCL (16x2 LCD SCL, PCF8574 #2 SCL, PCF8574 #3 SCL)

### 3. 8× HC-SR04 Ultrasonic Sensors
- **VCC:** External 5V Rail
- **GND:** Ground Bus
- **TRIG Pins:** Direct to ESP32 GPIO
- **ECHO Pins:** Through 1kΩ / 2kΩ Divider (5V ➔ 3.33V) to ESP32 GPIO

| Slot | TRIG GPIO | ECHO GPIO | Divider Setup |
|------|-----------|-----------|---------------|
| G1 | 13 | 34 | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |
| G2 | 14 | 35 | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |
| G3 | 27 | 36 (VP) | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |
| G4 | 26 | 39 (VN) | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |
| F1 | 25 | 18 | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |
| F2 | 33 | 5 | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |
| F3 | 32 | 17 (TX2) | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |
| F4 | 19 | 16 (RX2) | ECHO ➔ 1kΩ ➔ ESP32 Pin ➔ 2kΩ ➔ GND |

### 4. 16 Slot LEDs (Active-LOW via PCF8574s)
Wiring: **3.3V ➔ 220Ω ➔ LED Anode (+) | LED Cathode (-) ➔ PCF8574 Pin**

- **PCF8574 #2 (Ground Floor, Address 0x26):**
  - G1: Green = P0, Red = P1
  - G2: Green = P2, Red = P3
  - G3: Green = P4, Red = P5
  - G4: Green = P6, Red = P7

- **PCF8574 #3 (First Floor, Address 0x25):**
  - F1: Green = P0, Red = P1
  - F2: Green = P2, Red = P3
  - F3: Green = P4, Red = P5
  - F4: Green = P6, Red = P7

### 5. Gate Servos
- **Entry Servo Signal:** ESP32 **GPIO23** (VCC ➔ External 5V, GND ➔ Common GND)
- **Exit Servo Signal:** ESP32 **GPIO15** (VCC ➔ External 5V, GND ➔ Common GND)
- **Gate Indicator LEDs:** **Removed per owner request** (GPIO4 and GPIO2 are free/unconnected)

---

## I²C Scan Verification Results (from t01_i2c_scan) - PASSED ☑

```text
=== ParkTrack 360 — I2C Scanner (16x2 LCD Version) ===

Scanning I2C bus (SDA=21, SCL=22) ...

  Found device at 0x25  <-- PCF8574 (A1 bridged / First Floor LEDs)
  Found device at 0x26  <-- PCF8574 (A0 bridged / Ground Floor LEDs)
  Found device at 0x27  <-- PCF8574 (Default address / 16x2 LCD Backpack)

Scan complete. Found 3 device(s).

=== I2C scan complete ===
```

## Sensor Test Results (from t02_hcsr04) - PASSED ☑

```text
G1: 10.1 cm | G2:  9.4 cm | G3:  6.5 cm | G4:  4.9 cm
F1:  9.1 cm | F2:  6.5 cm | F3:  5.8 cm | F4:  8.1 cm
---
(Hand placed over G1):
G1:  5.2 cm | G2:  9.4 cm | G3:  6.4 cm | G4:  4.9 cm
G1:  3.6 cm | G2:  7.4 cm | G3:  8.1 cm | G4:  6.2 cm
G1:  2.3 cm | G2:  8.4 cm | G3:  8.4 cm | G4:  6.2 cm
```

| Slot | Baseline empty (~cm) | Status |
|------|----------------------|--------|
| G1 | ~10.1 cm | ☑ OK |
| G2 | ~9.4 cm | ☑ OK |
| G3 | ~6.5 cm | ☑ OK |
| G4 | ~4.9 cm | ☑ OK |
| F1 | ~9.1 cm | ☑ OK |
| F2 | ~6.5 cm | ☑ OK |
| F3 | ~5.8 cm | ☑ OK |
| F4 | ~8.1 cm | ☑ OK |

## LED Test Results (from t03_leds) - PASSED ☑

```text
PCF8574 found at 0x26
PCF8574 found at 0x25

=== Pattern Test ===
Writing 0xAA to 0x26 and 0x25  (all slots vacant: all green ON, all red OFF)
Writing 0x55 to 0x26 and 0x25  (all slots occupied: all red ON, all green OFF)
Writing 0x00 to 0x26 and 0x25  (ALL LEDs ON)
Writing 0xFF to 0x26 and 0x25  (ALL LEDs OFF)

=== Individual LED Walk ===
Ground floor (0x26): P0..P7 (G1 green to G4 red) ☑ OK
First floor (0x25):  P0..P7 (F1 green to F4 red) ☑ OK

=== LED test complete ===
```

- Pattern 0xAA (All Vacant - Green ON): ☑ OK
- Pattern 0x55 (All Occupied - Red ON): ☑ OK
- Pattern 0x00 (All ON): ☑ OK
- Pattern 0xFF (All OFF): ☑ OK
- Individual LED Walk: ☑ OK

## Servo Test Results (from t04_servo) - PASSED ☑

- Entry Servo Sweep (GPIO23): ☑ OK
- Exit Servo Sweep (GPIO15): ☑ OK
