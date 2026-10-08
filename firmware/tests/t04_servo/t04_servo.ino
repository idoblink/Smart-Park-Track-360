/*
 * t04_servo.ino — Servo sweep test (entry + exit gates)
 *
 * PURPOSE: Sweep each servo from 0° to 90° and back,
 *          using gradual stepping (2° every 15ms) as
 *          specified in section 4.4.
 *
 * WIRING: Entry servo signal → GPIO23
 *         Exit servo signal  → GPIO15
 *         Servo VCC → external 5V supply (NOT from ESP32)
 *         Servo GND → common ground bus
 *         470-1000µF capacitor across the 5V servo rail
 *
 * EXPECTED OUTPUT (Serial, 115200 baud):
 *   === Servo Test ===
 *   Testing ENTRY servo (GPIO23)...
 *   Sweeping 0 -> 90 degrees (2 deg / 15ms steps)
 *   Sweeping 90 -> 0 degrees
 *   Testing EXIT servo (GPIO15)...
 *   Sweeping 0 -> 90 degrees (2 deg / 15ms steps)
 *   Sweeping 90 -> 0 degrees
 *   === Servo test complete ===
 *
 * VERIFY: Each servo should sweep smoothly open then closed.
 *         If jerky or ESP32 resets, check 5V supply and capacitor.
 *
 * NOTE: GPIO15 may cause the servo to twitch at boot. This is
 *       expected (boot-strap pin behaviour) and is acceptable.
 *
 * LIBRARY: ESP32Servo (install via Arduino Library Manager)
 */

#include <ESP32Servo.h>

#define PIN_SERVO_ENTRY  23
#define PIN_SERVO_EXIT   15

#define SERVO_CLOSED_DEG  0
#define SERVO_OPEN_DEG    90
#define SERVO_STEP_DEG    2
#define SERVO_STEP_MS     15
#define SERVO_MIN_US      500
#define SERVO_MAX_US      2400

Servo entryServo;
Servo exitServo;

void sweepServo(Servo &servo, const char* name, uint8_t pin) {
  Serial.print("Testing ");
  Serial.print(name);
  Serial.print(" servo (GPIO");
  Serial.print(pin);
  Serial.println(")...");

  // Attach and set to closed position
  servo.attach(pin, SERVO_MIN_US, SERVO_MAX_US);
  servo.write(SERVO_CLOSED_DEG);
  delay(500);

  // Sweep open
  Serial.print("  Sweeping ");
  Serial.print(SERVO_CLOSED_DEG);
  Serial.print(" -> ");
  Serial.print(SERVO_OPEN_DEG);
  Serial.println(" degrees (2 deg / 15ms steps)");

  for (int deg = SERVO_CLOSED_DEG; deg <= SERVO_OPEN_DEG; deg += SERVO_STEP_DEG) {
    servo.write(deg);
    delay(SERVO_STEP_MS);
  }
  servo.write(SERVO_OPEN_DEG);
  delay(1000);  // hold open

  // Sweep closed
  Serial.print("  Sweeping ");
  Serial.print(SERVO_OPEN_DEG);
  Serial.print(" -> ");
  Serial.print(SERVO_CLOSED_DEG);
  Serial.println(" degrees");

  for (int deg = SERVO_OPEN_DEG; deg >= SERVO_CLOSED_DEG; deg -= SERVO_STEP_DEG) {
    servo.write(deg);
    delay(SERVO_STEP_MS);
  }
  servo.write(SERVO_CLOSED_DEG);
  delay(500);

  servo.detach();
  Serial.println("  Done.");
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ParkTrack 360 — Servo Test ===");
  Serial.println();
  Serial.println("Settings:");
  Serial.print("  Closed angle: "); Serial.print(SERVO_CLOSED_DEG); Serial.println(" deg");
  Serial.print("  Open angle:   "); Serial.print(SERVO_OPEN_DEG);   Serial.println(" deg");
  Serial.print("  Step:         "); Serial.print(SERVO_STEP_DEG);   Serial.println(" deg");
  Serial.print("  Step delay:   "); Serial.print(SERVO_STEP_MS);    Serial.println(" ms");
  Serial.print("  Pulse range:  "); Serial.print(SERVO_MIN_US);
  Serial.print("-"); Serial.print(SERVO_MAX_US); Serial.println(" us");
  Serial.println();

  sweepServo(entryServo, "ENTRY", PIN_SERVO_ENTRY);
  delay(1000);
  sweepServo(exitServo, "EXIT", PIN_SERVO_EXIT);

  Serial.println("=== Servo test complete ===");
  Serial.println("If a servo didn't move, check:");
  Serial.println("  - Signal wire to the correct GPIO");
  Serial.println("  - VCC to external 5V (NOT ESP32 pins)");
  Serial.println("  - GND to common ground bus");
  Serial.println("  - Capacitor across 5V rail near servos");
}

void loop() {
  // Nothing to do
}
