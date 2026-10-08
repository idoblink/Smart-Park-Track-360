/*
 * t02_hcsr04.ino — HC-SR04 ultrasonic sensor test
 *
 * PURPOSE: Read each of the 8 HC-SR04 sensors one at a time
 *          and print distance in cm. Verifies wiring, ECHO
 *          voltage dividers, and sensor operation.
 *
 * WIRING: Per spec section 3.4 pin map. Each ECHO line through
 *         1kΩ + 2kΩ voltage divider. Sensors on external 5V.
 *
 * EXPECTED OUTPUT (Serial, 115200 baud):
 *   === HC-SR04 Sensor Test (continuous) ===
 *   G1:  12.3 cm | G2:  12.1 cm | G3:  12.5 cm | G4:  12.2 cm
 *   F1:  12.4 cm | F2:  12.3 cm | F3:  12.6 cm | F4:  12.1 cm
 *   ---
 *   (repeats every ~500ms)
 *
 * TEST: Place a hand or car ~5cm above each sensor. The distance
 *       should drop accordingly. "timeout" means no echo received
 *       (check wiring or divider for that sensor).
 */

static const char* SLOT_NAMES[8] = {
  "G1", "G2", "G3", "G4", "F1", "F2", "F3", "F4"
};

static const uint8_t TRIG_PINS[8] = {13, 14, 27, 26, 25, 33, 32, 19};
static const uint8_t ECHO_PINS[8] = {34, 35, 36, 39, 18,  5, 17, 16};

#define ECHO_TIMEOUT_US  8000   // ~137 cm max
#define SENSOR_GAP_MS    15     // minimum gap between sensors

float readDistanceCm(uint8_t trigPin, uint8_t echoPin) {
  // Send 10µs trigger pulse
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read echo duration
  long duration = pulseIn(echoPin, HIGH, ECHO_TIMEOUT_US);

  if (duration == 0) {
    return -1.0f;  // timeout
  }

  return duration / 58.3f;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=== ParkTrack 360 — HC-SR04 Sensor Test ===");
  Serial.println();
  Serial.println("Pin map:");

  for (int i = 0; i < 8; i++) {
    Serial.print("  ");
    Serial.print(SLOT_NAMES[i]);
    Serial.print(": TRIG=GPIO");
    Serial.print(TRIG_PINS[i]);
    Serial.print(", ECHO=GPIO");
    Serial.println(ECHO_PINS[i]);

    pinMode(TRIG_PINS[i], OUTPUT);
    digitalWrite(TRIG_PINS[i], LOW);
    pinMode(ECHO_PINS[i], INPUT);
  }

  Serial.println();
  Serial.println("Reading all 8 sensors continuously...");
  Serial.println("Place hand or car above each sensor to verify.");
  Serial.println();
}

void loop() {
  float distances[8];

  // Read all 8 sensors sequentially
  for (int i = 0; i < 8; i++) {
    distances[i] = readDistanceCm(TRIG_PINS[i], ECHO_PINS[i]);
    delay(SENSOR_GAP_MS);
  }

  // Print ground floor
  for (int i = 0; i < 4; i++) {
    Serial.print(SLOT_NAMES[i]);
    Serial.print(": ");
    if (distances[i] < 0) {
      Serial.print("timeout ");
    } else {
      if (distances[i] < 10.0f) Serial.print(" ");
      Serial.print(distances[i], 1);
      Serial.print(" cm");
    }
    if (i < 3) Serial.print(" | ");
  }
  Serial.println();

  // Print first floor
  for (int i = 4; i < 8; i++) {
    Serial.print(SLOT_NAMES[i]);
    Serial.print(": ");
    if (distances[i] < 0) {
      Serial.print("timeout ");
    } else {
      if (distances[i] < 10.0f) Serial.print(" ");
      Serial.print(distances[i], 1);
      Serial.print(" cm");
    }
    if (i < 7) Serial.print(" | ");
  }
  Serial.println();
  Serial.println("---");

  delay(500);
}
