# ParkTrack 360 — Wiring Verification Record

## Board

- **Module:** ESP32 DevKit V1 (30-pin)
- **Variant:** ☐ WROOM (OK) / ☐ WROVER (PROBLEM — notify owner)
- **PSRAM size from t06_psram:** _________ bytes

## I²C Scan Results (from t01_i2c_scan)

Paste serial output here:

```
(paste output here)
```

### Confirmed Addresses

| Device | Expected | Found | Notes |
|--------|----------|-------|-------|
| SSD1306 OLED | 0x3C | | 0x3D on some modules |
| PCF8574 #1 (Ground floor) | 0x20 | | 0x38 if PCF8574A |
| PCF8574 #2 (First floor) | 0x21 | | 0x39 if PCF8574A |

### OLED

- Resolution: ☐ 128×64 / ☐ 128×32
- I²C address confirmed: _______

### PCF8574 Type

- ☐ PCF8574 (addresses 0x20–0x27)
- ☐ PCF8574A (addresses 0x38–0x3F)

## HC-SR04 Sensor Test (from t02_hcsr04)

Paste serial output here:

```
(paste output here)
```

### Sensor Check

| Slot | TRIG GPIO | ECHO GPIO | Baseline (~empty, cm) | With car (~cm) | Status |
|------|-----------|-----------|----------------------|----------------|--------|
| G1 | 13 | 34 | | | ☐ OK / ☐ FAIL |
| G2 | 14 | 35 | | | ☐ OK / ☐ FAIL |
| G3 | 27 | 36 (VP) | | | ☐ OK / ☐ FAIL |
| G4 | 26 | 39 (VN) | | | ☐ OK / ☐ FAIL |
| F1 | 25 | 18 | | | ☐ OK / ☐ FAIL |
| F2 | 33 | 5 | | | ☐ OK / ☐ FAIL |
| F3 | 32 | 17 (TX2) | | | ☐ OK / ☐ FAIL |
| F4 | 19 | 16 (RX2) | | | ☐ OK / ☐ FAIL |

## LED Test (from t03_leds)

### Pattern Test

| Pattern | Hex | Expected | Observed |
|---------|-----|----------|----------|
| All vacant | 0xAA | All greens ON, all reds OFF | ☐ OK / ☐ FAIL |
| All occupied | 0x55 | All reds ON, all greens OFF | ☐ OK / ☐ FAIL |
| All ON | 0x00 | All 16 LEDs ON | ☐ OK / ☐ FAIL |
| All OFF | 0xFF | All 16 LEDs OFF | ☐ OK / ☐ FAIL |

### Individual LED Walk

| LED | Lit correctly? | Notes |
|-----|---------------|-------|
| G1 green (0x20 P0) | ☐ | |
| G1 red (0x20 P1) | ☐ | |
| G2 green (0x20 P2) | ☐ | |
| G2 red (0x20 P3) | ☐ | |
| G3 green (0x20 P4) | ☐ | |
| G3 red (0x20 P5) | ☐ | |
| G4 green (0x20 P6) | ☐ | |
| G4 red (0x20 P7) | ☐ | |
| F1 green (0x21 P0) | ☐ | |
| F1 red (0x21 P1) | ☐ | |
| F2 green (0x21 P2) | ☐ | |
| F2 red (0x21 P3) | ☐ | |
| F3 green (0x21 P4) | ☐ | |
| F3 red (0x21 P5) | ☐ | |
| F4 green (0x21 P6) | ☐ | |
| F4 red (0x21 P7) | ☐ | |

## Servo Test (from t04_servo)

| Gate | GPIO | Sweeps smoothly? | Notes |
|------|------|-------------------|-------|
| Entry | 23 | ☐ OK / ☐ FAIL | |
| Exit | 15 | ☐ OK / ☐ FAIL | GPIO15 may twitch at boot (expected) |

- Did the ESP32 reset during servo movement? ☐ Yes / ☐ No
- External 5V supply used? ☐ Yes / ☐ No
- Capacitor installed? ☐ Yes / ☐ No

## Gate LED Pair Test (from t05_gateleds)

| Pair | GPIO | GREEN when HIGH? | RED when LOW? | Notes |
|------|------|-------------------|---------------|-------|
| Entry | 4 | ☐ OK / ☐ FAIL | ☐ OK / ☐ FAIL | |
| Exit | 2 | ☐ OK / ☐ FAIL | ☐ OK / ☐ FAIL | Upload issues? Disconnect LED lead |

## Arduino IDE Configuration

- **Board:** ESP32 Dev Module
- **Espressif core version:** _______
- **Upload speed:** 921600 (default)
- **COM port:** _______

## Libraries Used

| Library | Version | Source |
|---------|---------|--------|
| Wire | (built-in) | ESP32 core |
| ESP32Servo | | Arduino Library Manager |
| Adafruit GFX | | Arduino Library Manager |
| Adafruit SSD1306 | | Arduino Library Manager |
| WebSockets (Markus Sattler) | | Arduino Library Manager |
| ArduinoJson | v7.x | Arduino Library Manager |

## Wiring Verification Checklist (Appendix B)

- [ ] All grounds common (external 5V supply, ESP32, sensors, PCF8574s, servos, LED returns)
- [ ] Servo 5V and sensor 5V come from the external supply, not from the ESP32
- [ ] Every ECHO goes through 1kΩ → junction (to ESP32) → 2kΩ → GND
- [ ] PCF8574 and OLED powered from 3.3V; SDA = 21, SCL = 22
- [ ] Slot LEDs: 3.3V → 220Ω → anode, cathode → PCF8574 pin
- [ ] Gate pair: green GPIO → 220Ω → LED → GND; red 3.3V → 220Ω → LED → same GPIO
- [ ] Capacitor across servo 5V rail
- [ ] Nothing on GPIO0/12; GPIO1 unconnected
