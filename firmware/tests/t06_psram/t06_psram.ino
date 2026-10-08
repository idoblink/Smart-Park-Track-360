/*
 * t06_psram.ino — PSRAM check
 * 
 * PURPOSE: Confirm the ESP32 module is WROOM (no PSRAM),
 *          not WROVER (has PSRAM and uses GPIO16/17).
 *          GPIO16 and GPIO17 are used for ECHO pins F3 and F4.
 *
 * EXPECTED OUTPUT (Serial, 115200 baud):
 *   PSRAM Size: 0 bytes
 *   Result: WROOM module (OK — GPIO16/17 are available)
 *
 * If PSRAM > 0, the module is WROVER and GPIO16/17 cannot be used.
 *   PSRAM Size: 4194304 bytes
 *   Result: WROVER module (PROBLEM — GPIO16/17 are used by PSRAM)
 *   >> Notify the owner before proceeding. <<
 */

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ParkTrack 360 — PSRAM Check ===");
  Serial.println();

  uint32_t psramSize = ESP.getPsramSize();
  Serial.print("PSRAM Size: ");
  Serial.print(psramSize);
  Serial.println(" bytes");
  Serial.println();

  if (psramSize == 0) {
    Serial.println("Result: WROOM module (OK -- GPIO16/17 are available)");
  } else {
    Serial.println("Result: WROVER module (PROBLEM -- GPIO16/17 are used by PSRAM)");
    Serial.println(">> Notify the owner before proceeding. <<");
  }

  Serial.println();
  Serial.println("=== PSRAM check complete ===");
}

void loop() {
  // Nothing to do
}
