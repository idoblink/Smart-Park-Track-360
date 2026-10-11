/*
 * servo_dual_sweep.ino — Direct Hardware Diagnostic for Both Servos
 * 
 * Tests ENTRY (GPIO 4) and EXIT (GPIO 15) directly with zero external code.
 * Sweeps Entry 0° -> 90° -> 0°, then Exit 0° -> 90° -> 0°.
 */

#include <Arduino.h>
#include <ESP32Servo.h>

#define PIN_ENTRY  4    // If using GPIO 23, change to 23
#define PIN_EXIT   15

Servo entryServo;
Servo exitServo;

void sweep(Servo &s, const char* name, int pin) {
  Serial.printf("\n>>> Testing %s servo on GPIO %d <<<\n", name, pin);
  
  // Sweep to 90 degrees
  Serial.println("  Moving to 90° (OPEN)...");
  for (int pos = 0; pos <= 90; pos += 2) {
    s.write(pos);
    delay(15);
  }
  s.write(90);
  delay(1500);

  // Sweep back to 0 degrees
  Serial.println("  Moving to 0° (CLOSED)...");
  for (int pos = 90; pos >= 0; pos -= 2) {
    s.write(pos);
    delay(15);
  }
  s.write(0);
  delay(1500);

  Serial.printf(">>> %s test complete <<<\n", name);
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  Serial.println("\n============================================");
  Serial.println("   ParkTrack 360 — Dual Servo Direct Test");
  Serial.println("============================================");

  // Standard attach with SG90 safe pulse widths
  int ch1 = entryServo.attach(PIN_ENTRY, 544, 2400);
  int ch2 = exitServo.attach(PIN_EXIT,   544, 2400);

  Serial.printf("[Init] Entry servo (pin %d) -> Channel %d\n", PIN_ENTRY, ch1);
  Serial.printf("[Init] Exit  servo (pin %d) -> Channel %d\n", PIN_EXIT,  ch2);

  entryServo.write(0);
  exitServo.write(0);
  delay(1000);
}

void loop() {
  sweep(entryServo, "ENTRY", PIN_ENTRY);
  delay(1000);

  sweep(exitServo, "EXIT", PIN_EXIT);
  delay(1000);
}
