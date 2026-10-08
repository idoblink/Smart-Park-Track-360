# ParkTrack 360 — Questions for the Owner

Items that need your answer before proceeding. The spec says to write concerns here rather than guess.

---

## From Step 1 (Hardware Checks)

### Q1. OLED resolution
The spec assumes **128×64**. After running `t01_i2c_scan`, please confirm:
- Is your OLED module 128×64 or 128×32?
- What I²C address did the scan find? (expected 0x3C)

### Q2. PCF8574 or PCF8574A?
The I²C scan will tell us. If your modules respond at 0x38/0x39 instead of 0x20/0x21, they are PCF8574A and we need to update `config.h`.

### Q3. Servo angles
The defaults are: closed = 0°, open = 90°. After running `t04_servo`:
- Do these angles work for your physical barrier gate design?
- Do you need different angles?

### Q4. Toy car heights
Please measure your tallest and shortest Hot Wheels car (roof height in cm). This sets the `OCCUPIED_MARGIN_CM` and sensor mounting height.
- Tallest car: ___ cm
- Shortest car: ___ cm

### Q5. Sensor mounting style
- **Overhead** (sensor faces down from the deck above): default
- **End-wall** (sensor faces along the slot from the back wall): fallback if overhead is unreliable

Which are you using?

### Q6. Network option (section 2.1)
Which will you use?
- **A.** Windows Mobile Hotspot (recommended)
- **B.** Phone hotspot
- **C.** Home/lab router

What is the laptop's IP address on that network?

### Q7. Training location
Do you have an NVIDIA GPU with CUDA for YOLO training?
- If yes: we train locally
- If no: we'll use Google Colab (I'll provide a notebook)

---

*Add new questions below as they come up during later steps.*
