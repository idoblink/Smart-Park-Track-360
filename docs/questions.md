# ParkTrack 360 — Questions for the Owner

Items that need your answer before proceeding. The spec says to write concerns here rather than guess.

---

## From Step 1 (Hardware Checks)

### Q1. Display Hardware
- **Confirmed:** **16x2 Character LCD** with PCF8574 I²C backpack (`JHD 162A`). OLED is NOT used anywhere.
- **Library:** `LiquidCrystal_I2C`

### Q2. PCF8574 Expanders (Total 3)
- **LCD Backpack:** Address `0x27` (default, no solder bridge)
- **Ground Floor Slot LEDs:** Address `0x26` (A0 pad bridged)
- **First Floor Slot LEDs:** Address `0x25` (A1 pad bridged)

### Gate Indicator LEDs
- **Removed completely per owner request.** GPIO4 and GPIO2 remain free/unconnected.

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
