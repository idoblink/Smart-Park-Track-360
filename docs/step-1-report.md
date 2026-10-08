# Step 1 Report — Hardware Checks

**Date:** 2026-10-08
**Status:** Ready for owner testing

---

## What was built

Six test sketches in `firmware/tests/`, each verifying a specific hardware subsystem:

| Test | Folder | Purpose |
|------|--------|---------|
| t01 | `firmware/tests/t01_i2c_scan/` | Scan I²C bus: find OLED and PCF8574 addresses |
| t02 | `firmware/tests/t02_hcsr04/` | Read all 8 HC-SR04 sensors continuously |
| t03 | `firmware/tests/t03_leds/` | Test all 16 slot LEDs via both PCF8574 expanders |
| t04 | `firmware/tests/t04_servo/` | Sweep both servos (entry & exit gates) |
| t05 | `firmware/tests/t05_gateleds/` | Test gate indicator LED pairs |
| t06 | `firmware/tests/t06_psram/` | Check PSRAM (WROOM vs WROVER) |

Also created:
- `docs/wiring.md` — Wiring verification record (fill in as you test)
- `docs/questions.md` — Open questions that need your answers

---

## How to run each test

### Prerequisites
1. Install **Arduino IDE 2.x**
2. Install the **ESP32 board package** (Espressif Systems) via Board Manager
3. Select board: **ESP32 Dev Module**
4. Select the correct COM port
5. Set upload speed to **921600** (default)

### For each test sketch:
1. In Arduino IDE: **File → Open** → navigate to the `.ino` file
2. Click **Upload** (→ button)
3. Open **Serial Monitor** (magnifying glass icon, top right)
4. Set baud rate to **115200**
5. Read the output and compare with the expected output below

### Libraries needed (install via Library Manager):
- **t01–t03:** No external libraries (Wire is built-in)
- **t04:** `ESP32Servo` by Kevin Harrington
- **t05–t06:** No external libraries

---

## Recommended test order

### 1. t06_psram (do this FIRST — no wiring needed)

Just the ESP32 plugged into USB. No other wiring.

**Expected output:**
```
=== ParkTrack 360 — PSRAM Check ===

PSRAM Size: 0 bytes

Result: WROOM module (OK -- GPIO16/17 are available)

=== PSRAM check complete ===
```

**If PSRAM > 0:** STOP and tell me. Your module is WROVER and GPIO16/17 (used for F3 and F4 ECHO) cannot be used. We need to discuss alternatives.

---

### 2. t01_i2c_scan (wire I²C bus only)

Wire: SDA→GPIO21, SCL→GPIO22, all I²C modules to 3.3V + GND.

**Expected output:**
```
=== ParkTrack 360 — I2C Scanner ===

Scanning I2C bus (SDA=21, SCL=22) ...

  Found device at 0x20  <-- PCF8574 (address offset 0)
  Found device at 0x21  <-- PCF8574 (address offset 1)
  Found device at 0x3C  <-- SSD1306 OLED

Scan complete. Found 3 device(s).

=== I2C scan complete ===
```

**Record** the addresses in `docs/wiring.md`.

If addresses are 0x38/0x39 instead of 0x20/0x21, your modules are **PCF8574A** — tell me and I'll update `config.h`.

---

### 3. t02_hcsr04 (wire sensors to 5V supply + ECHO dividers)

Wire all 8 sensors per the pin map. **External 5V supply required.**

**Expected output (example — distances will vary):**
```
G1:  12.3 cm | G2:  12.1 cm | G3:  12.5 cm | G4:  12.2 cm
F1:  12.4 cm | F2:  12.3 cm | F3:  12.6 cm | F4:  12.1 cm
---
```

**Test:** Place your hand ~5cm above each sensor — the distance should drop. "timeout" means check that sensor's wiring/divider.

---

### 4. t03_leds (with I²C already wired)

All 16 slot LEDs must be wired to the PCF8574 pins.

**What to watch:**
- Pattern 0xAA: all **greens ON**, all reds OFF (vacant)
- Pattern 0x55: all **reds ON**, all greens OFF (occupied)
- Pattern 0x00: all 16 LEDs ON
- Pattern 0xFF: all LEDs OFF
- Individual walk: each LED lights alone for 500ms

**If using PCF8574A:** Edit the two `#define` lines at the top of the sketch to `0x38` and `0x39` before uploading.

---

### 5. t04_servo (wire servos to external 5V)

**Important:** Servo VCC must come from the external 5V supply, **not** from the ESP32. Connect the capacitor across the 5V rail near the servos.

**What to watch:** Each servo sweeps smoothly from 0° to 90° and back. If the ESP32 resets during the sweep, the supply can't handle the current — check the capacitor and supply rating.

---

### 6. t05_gateleds (wire gate LED pairs)

**What to watch:**
- GPIO HIGH → green LED lit, red off
- GPIO LOW → red LED lit, green off

**Note:** If upload fails, disconnect the exit LED lead from GPIO2 (boot-strap pin) and retry.

---

## What to paste back

After running all 6 tests, please:

1. **Paste the serial output** from t01 (I²C scan) and t06 (PSRAM) into `docs/wiring.md`
2. **Fill in** the sensor distances table in `docs/wiring.md`
3. **Check off** the LED and servo results
4. **Answer the questions** in `docs/questions.md` (especially OLED size, PCF8574 type, car heights, network option)
5. **Tell me** the results so I can proceed to Step 2 (firmware standalone)

---

## What the owner must verify on hardware

| Check | How | Pass criteria |
|-------|-----|---------------|
| PSRAM = 0 | t06 serial output | "WROOM module (OK)" |
| 3 I²C devices found | t01 serial output | 0x20, 0x21, 0x3C (or equivalent) |
| All 8 sensors read | t02 serial output | No "timeout", distances change with hand |
| All 16 slot LEDs work | t03 visual + serial | Every LED lights in the walk, patterns match |
| Both servos sweep | t04 visual | Smooth 0°→90°→0°, no ESP32 reset |
| Both gate LED pairs work | t05 visual | Green/red toggle correctly per GPIO state |
