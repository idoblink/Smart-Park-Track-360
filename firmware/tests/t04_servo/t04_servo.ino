/*
 * t04_servo.ino — Servo sweep test with pulse width tuning
 *
 * PURPOSE: Sweep each servo from 0° to 90° and back.
 *          Fixes exit servo twitch/range issues by using
 *          standard Servo library pulse widths (544us - 2400us).
 *
 * WIRING: Entry servo signal → GPIO23
 *         Exit servo signal  → GPIO15
 *         Servo VCC → external 5V supply
 *         Servo GND → common ground bus
 */

#include <ESP32Servo.h>

#define PIN_SERVO_ENTRY  23
#define PIN_SERVO_EXIT   15

#define SERVO_CLOSED_DEG  0
#define SERVO_OPEN_DEG    90
#define SERVO_STEP_DEG    2
#define SERVO_STEP_MS     15

// Standard SG90 servo pulse limits (544us - 2400us prevents mechanical hitting)
#define SERVO_MIN_US      544
#define SERVO_MAX_US      2400

Servo entryServo;
Servo exitServo;

void sweepServo(Servo &servo, const char* name, uint8_t pin) {
  Serial.print("Testing ");
  Serial.print(name);
  Serial.print(" servo (GPIO");
  Serial.print(pin);
  Serial.println(")...");

  // Allow ESP32 signal to stabilize before attach
  delay(100);
  servo.attach(pin, SERVO_MIN_US, SERVO_MAX_US);
  servo.write(SERVO_CLOSED_DEG);
  delay(500);

  // Sweep open
  Serial.print("  Sweeping ");
  Serial.print(SERVO_CLOSED_DEG);
  Serial.print(" -> ");
  Serial.print(SERVO_OPEN_DEG);
  Serial.println(" degrees");

  for (int deg = SERVO_CLOSED_DEG; deg <= SERVO_OPEN_DEG; deg += SERVO_STEP_DEG) {
    servo.write(deg);
    delay(SERVO_STEP_MS);
  }
  servo.write(SERVO_OPEN_DEG);
  delay(1500);  // hold open

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
  Serial.println("=== ParkTrack 360 — Servo Test (Tuned Pulse Width) ===");
  Serial.println();

  // Allow system power to settle
  delay(500);

  sweepServo(entryServo, "ENTRY", PIN_SERVO_ENTRY);
  delay(1000);
  sweepServo(exitServo, "EXIT", PIN_SERVO_EXIT);

  Serial.println("=== Servo test complete ===");
}

void loop() {
  // Nothing to do
}
