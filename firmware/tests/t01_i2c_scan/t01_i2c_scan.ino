/*
 * t01_i2c_scan.ino — I²C bus scanner
 *
 * PURPOSE: Find all devices on the I²C bus (SDA=GPIO21, SCL=GPIO22).
 *          Expected devices:
 *            - SSD1306 OLED at 0x3C (or 0x3D on some modules)
 *            - PCF8574 #1 (ground floor) at 0x20 (or 0x38 if PCF8574A)
 *            - PCF8574 #2 (first floor) at 0x21 (or 0x39 if PCF8574A)
 *
 * WIRING: SDA → GPIO21, SCL → GPIO22
 *         All I²C devices powered from ESP32 3.3V + common GND
 *
 * EXPECTED OUTPUT (Serial, 115200 baud):
 *   Scanning I2C bus (SDA=21, SCL=22) ...
 *   Found device at 0x20
 *   Found device at 0x21
 *   Found device at 0x3C
 *   Scan complete. Found 3 device(s).
 *
 * RECORD: Paste the serial output into docs/wiring.md
 */

#include <Wire.h>

#define PIN_SDA 21
#define PIN_SCL 22

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ParkTrack 360 — I2C Scanner ===");
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

      // Identify known devices
      if (addr == 0x3C || addr == 0x3D) {
        Serial.print("  <-- SSD1306 OLED");
      } else if (addr >= 0x20 && addr <= 0x27) {
        Serial.print("  <-- PCF8574 (address offset ");
        Serial.print(addr - 0x20);
        Serial.print(")");
      } else if (addr >= 0x38 && addr <= 0x3F) {
        Serial.print("  <-- PCF8574A (address offset ");
        Serial.print(addr - 0x38);
        Serial.print(")");
      }
      Serial.println();
      found++;
    }
  }

  Serial.println();
  Serial.print("Scan complete. Found ");
  Serial.print(found);
  Serial.println(" device(s).");

  if (found == 0) {
    Serial.println();
    Serial.println("!! No devices found. Check wiring:");
    Serial.println("   - SDA to GPIO21, SCL to GPIO22");
    Serial.println("   - 3.3V power to each module");
    Serial.println("   - All GNDs connected to the common ground bus");
    Serial.println("   - Pull-up resistors present (most breakouts have them)");
  }

  Serial.println();
  Serial.println("=== I2C scan complete ===");
}

void loop() {
  // Nothing to do — scan runs once
}
