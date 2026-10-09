/*
 * t03_leds.ino — PCF8574 LED test (slot LEDs)
 *
 * PURPOSE: Walk through all 16 slot LEDs on both PCF8574 expanders
 *          using the spec's test patterns: 0xAA, 0x55, 0xFF, 0x00.
 *          Also walks individual LEDs one by one.
 *
 * WIRING: I²C bus SDA=GPIO21, SCL=GPIO22.
 *         PCF8574 #1 at 0x20 (ground floor G1-G4 LEDs)
 *         PCF8574 #2 at 0x21 (first floor F1-F4 LEDs)
 *         Active-LOW: writing 0 to a bit turns the LED ON.
 *
 * ADDRESSES: If using PCF8574A modules, change to 0x38 and 0x39.
 *
 * EXPECTED OUTPUT (Serial, 115200 baud):
 *   === LED Test: Pattern Walk ===
 *   Writing 0xAA to 0x20 (all vacant: greens ON)
 *   Writing 0xAA to 0x21 (all vacant: greens ON)
 *   ... (pause 2s between each pattern)
 *   === LED Test: Individual Walk ===
 *   0x20 P0 (G1 green) ON
 *   ... (each LED lights for 500ms)
 *
 * VERIFY: Watch the LEDs match the serial description.
 */

#include <Wire.h>

#define PIN_SDA  21
#define PIN_SCL  22

// Expander addresses matching your hardware setup (A0 bridged=0x26, A1 bridged=0x25)
#define ADDR_PCF_GROUND  0x26
#define ADDR_PCF_FIRST   0x25

// LED names for each bit on each expander
static const char* LED_NAMES_GROUND[8] = {
  "G1 green", "G1 red", "G2 green", "G2 red",
  "G3 green", "G3 red", "G4 green", "G4 red"
};
static const char* LED_NAMES_FIRST[8] = {
  "F1 green", "F1 red", "F2 green", "F2 red",
  "F3 green", "F3 red", "F4 green", "F4 red"
};

void writeExpander(uint8_t addr, uint8_t value) {
  Wire.beginTransmission(addr);
  Wire.write(value);
  uint8_t err = Wire.endTransmission();
  if (err != 0) {
    Serial.print("  !! I2C error ");
    Serial.print(err);
    Serial.print(" writing to 0x");
    Serial.println(addr, HEX);
  }
}

void testPattern(uint8_t pattern, const char* desc) {
  Serial.print("Writing 0x");
  if (pattern < 16) Serial.print("0");
  Serial.print(pattern, HEX);
  Serial.print(" to 0x");
  Serial.print(ADDR_PCF_GROUND, HEX);
  Serial.print(" and 0x");
  Serial.print(ADDR_PCF_FIRST, HEX);
  Serial.print("  (");
  Serial.print(desc);
  Serial.println(")");

  writeExpander(ADDR_PCF_GROUND, pattern);
  writeExpander(ADDR_PCF_FIRST, pattern);
  delay(2000);
}

void walkLEDs(uint8_t addr, const char* names[8]) {
  for (int bit = 0; bit < 8; bit++) {
    // All off (0xFF), then clear one bit to light it
    uint8_t val = 0xFF & ~(1 << bit);

    Serial.print("  0x");
    Serial.print(addr, HEX);
    Serial.print(" P");
    Serial.print(bit);
    Serial.print(" (");
    Serial.print(names[bit]);
    Serial.print(") ON  [byte=0x");
    if (val < 16) Serial.print("0");
    Serial.print(val, HEX);
    Serial.println("]");

    writeExpander(addr, val);
    delay(500);
    writeExpander(addr, 0xFF);  // all off
    delay(200);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ParkTrack 360 — PCF8574 LED Test ===");
  Serial.println();

  Wire.begin(PIN_SDA, PIN_SCL);

  // Verify both expanders are present
  for (uint8_t addr : {ADDR_PCF_GROUND, ADDR_PCF_FIRST}) {
    Wire.beginTransmission(addr);
    uint8_t err = Wire.endTransmission();
    if (err != 0) {
      Serial.print("!! PCF8574 NOT FOUND at 0x");
      Serial.print(addr, HEX);
      Serial.println(" — check wiring and address jumpers!");
    } else {
      Serial.print("PCF8574 found at 0x");
      Serial.println(addr, HEX);
    }
  }

  // Start with all LEDs off
  writeExpander(ADDR_PCF_GROUND, 0xFF);
  writeExpander(ADDR_PCF_FIRST, 0xFF);
  delay(1000);

  // --- Pattern test ---
  Serial.println();
  Serial.println("=== Pattern Test ===");
  Serial.println("Active-LOW: bit=0 means LED ON, bit=1 means LED OFF");
  Serial.println();

  testPattern(0xAA, "all slots vacant: all green ON, all red OFF");
  testPattern(0x55, "all slots occupied: all red ON, all green OFF");
  testPattern(0x00, "ALL LEDs ON");
  testPattern(0xFF, "ALL LEDs OFF");

  // --- Individual walk ---
  Serial.println();
  Serial.println("=== Individual LED Walk ===");
  Serial.println();

  Serial.println("Ground floor (0x20):");
  walkLEDs(ADDR_PCF_GROUND, LED_NAMES_GROUND);

  Serial.println();
  Serial.println("First floor (0x21):");
  walkLEDs(ADDR_PCF_FIRST, LED_NAMES_FIRST);

  // End with all off
  writeExpander(ADDR_PCF_GROUND, 0xFF);
  writeExpander(ADDR_PCF_FIRST, 0xFF);

  Serial.println();
  Serial.println("=== LED test complete ===");
  Serial.println("Verify each LED lit in the correct order.");
}

void loop() {
  // Nothing to do
}
