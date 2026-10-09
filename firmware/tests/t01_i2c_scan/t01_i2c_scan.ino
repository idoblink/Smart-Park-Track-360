/*
 * t01_i2c_scan.ino — I²C bus scanner (16x2 LCD + 2x PCF8574 version)
 *
 * PURPOSE: Find all 3 devices on the I²C bus (SDA=GPIO21, SCL=GPIO22).
 *          Expected devices:
 *            - PCF8574 #1 (16x2 LCD Display Backpack) at 0x27 (or 0x3F)
 *            - PCF8574 #2 (Ground floor LEDs) at 0x26 (A0 bridged with solder)
 *            - PCF8574 #3 (First floor LEDs) at 0x25 (A1 bridged with solder)
 *
 * WIRING: SDA → GPIO21, SCL → GPIO22
 *         All 3 I²C modules powered from ESP32 3.3V + common GND
 *
 * EXPECTED OUTPUT (Serial, 115200 baud):
 *   Scanning I2C bus (SDA=21, SCL=22) ...
 *   Found device at 0x25  <-- PCF8574 (First Floor LEDs)
 *   Found device at 0x26  <-- PCF8574 (Ground Floor LEDs)
 *   Found device at 0x27  <-- PCF8574 (16x2 LCD Backpack)
 *   Scan complete. Found 3 device(s).
 */

#include <Wire.h>

#define PIN_SDA 21
#define PIN_SCL 22

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ParkTrack 360 — I2C Scanner (16x2 LCD Version) ===");
  Serial.println();

  Wire.begin(PIN_SDA, PIN_SCL);

  Serial.print("Scanning I2C bus (SDA=");
  Serial.print(PIN_SDA);
  Serial.print(", SCL=");
  Serial.print(PIN_SCL);
  Serial.println(") ...");
  Serial.println();

  int found = 0;
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("  Found device at 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);

      if (addr == 0x27 || addr == 0x3F) {
        Serial.print("  <-- PCF8574 (Default address / 16x2 LCD Backpack)");
      } else if (addr == 0x26) {
        Serial.print("  <-- PCF8574 (A0 bridged / Ground Floor LEDs)");
      } else if (addr == 0x25) {
        Serial.print("  <-- PCF8574 (A1 bridged / First Floor LEDs)");
      } else if (addr >= 0x20 && addr <= 0x27) {
        Serial.print("  <-- PCF8574 expander");
      } else if (addr >= 0x38 && addr <= 0x3F) {
        Serial.print("  <-- PCF8574A expander");
      }
      Serial.println();
      found++;
    }
  }

  Serial.println();
  Serial.print("Scan complete. Found ");
  Serial.print(found);
  Serial.println(" device(s).");

  if (found < 3) {
    Serial.println();
    Serial.println("!! Found fewer than 3 devices. Check:");
    Serial.println("   1. Have you set different addresses for the expanders? (e.g. solder A0 on one, A1 on the second)");
    Serial.println("   2. Are all 3 modules powered with 3.3V and GND?");
    Serial.println("   3. Are SDA to GPIO21 and SCL to GPIO22 connected securely?");
  }

  Serial.println();
  Serial.println("=== I2C scan complete ===");
}

void loop() {
  // Nothing to do
}
