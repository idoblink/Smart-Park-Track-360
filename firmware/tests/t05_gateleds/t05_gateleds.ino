/*
 * t05_gateleds.ino — Gate indicator LED pair test
 *
 * PURPOSE: Test the complementary gate LED pairs.
 *          Each pair uses ONE GPIO: HIGH = green on / red off,
 *          LOW = red on / green off.
 *
 * WIRING (per spec section 3.4):
 *   Entry pair (GPIO4):
 *     Green: GPIO4 → 220Ω → green LED → GND
 *     Red:   3.3V → 220Ω → red LED → GPIO4
 *   Exit pair (GPIO2):
 *     Green: GPIO2 → 220Ω → green LED → GND
 *     Red:   3.3V → 220Ω → red LED → GPIO2
 *
 * EXPECTED OUTPUT (Serial, 115200 baud):
 *   Entry: GREEN on (red off)  — verify green lit, red off
 *   Entry: RED on (green off)  — verify red lit, green off
 *   Exit:  GREEN on (red off)  — verify green lit, red off
 *   Exit:  RED on (green off)  — verify red lit, green off
 *   ... (cycles every 2 seconds)
 *
 * NOTE: GPIO2 is a boot-strap pin. If upload fails with a
 *       boot-mode error, disconnect the exit LED lead and retry.
 */

#define PIN_GATELED_ENTRY  4
#define PIN_GATELED_EXIT   2

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ParkTrack 360 — Gate LED Pair Test ===");
  Serial.println();
  Serial.println("Wiring: GPIO HIGH = green ON / red OFF");
  Serial.println("        GPIO LOW  = red ON / green OFF");
  Serial.println();

  pinMode(PIN_GATELED_ENTRY, OUTPUT);
  pinMode(PIN_GATELED_EXIT, OUTPUT);

  // Start with both showing red (closed state)
  digitalWrite(PIN_GATELED_ENTRY, LOW);
  digitalWrite(PIN_GATELED_EXIT, LOW);
}

void loop() {
  // Entry GREEN
  digitalWrite(PIN_GATELED_ENTRY, HIGH);
  Serial.println("Entry: GREEN on (red off)  -- verify green LED lit");
  delay(2000);

  // Entry RED
  digitalWrite(PIN_GATELED_ENTRY, LOW);
  Serial.println("Entry: RED on (green off)  -- verify red LED lit");
  delay(2000);

  // Exit GREEN
  digitalWrite(PIN_GATELED_EXIT, HIGH);
  Serial.println("Exit:  GREEN on (red off)  -- verify green LED lit");
  delay(2000);

  // Exit RED
  digitalWrite(PIN_GATELED_EXIT, LOW);
  Serial.println("Exit:  RED on (green off)  -- verify red LED lit");
  delay(2000);

  // Both green (free slots > 0, exit gate open)
  digitalWrite(PIN_GATELED_ENTRY, HIGH);
  digitalWrite(PIN_GATELED_EXIT, HIGH);
  Serial.println("Both:  GREEN on            -- both should be green");
  delay(2000);

  // Both red (full parking, exit gate closed)
  digitalWrite(PIN_GATELED_ENTRY, LOW);
  digitalWrite(PIN_GATELED_EXIT, LOW);
  Serial.println("Both:  RED on              -- both should be red");
  delay(2000);

  Serial.println("--- cycle ---");
  Serial.println();
}
