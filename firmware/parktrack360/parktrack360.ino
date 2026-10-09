/* =====================================================================
 *  ParkTrack 360 — Main Firmware Sketch
 *  Version: 1.1.0
 *
 *  Hardware configuration:
 *    - ESP32 DevKit V1 (30-pin, WROOM module)
 *    - 8× HC-SR04 ultrasonic sensors (G1..G4, F1..F4)
 *    - 2× PCF8574 I²C expanders for 16 slot LEDs (0x26, 0x25)
 *    - 1× 16×2 Character LCD with PCF8574 backpack (0x27)
 *    - 2× SG90/MG90S servo motors for entry (GPIO23) and exit (GPIO15) gates
 *    - Wi-Fi + WebSocket client to Laptop server (FastAPI, 8000)
 * =====================================================================*/

#include <Arduino.h>
#include <Wire.h>

#include "config.h"
#include "storage.h"
#include "display.h"
#include "leds.h"
#include "sensors.h"
#include "slots.h"
#include "gates.h"
#include "net.h"
#include "serial_cmd.h"

void setup() {
    // 1. Initialize Serial monitor
    Serial.begin(115200);
    delay(500);

    Serial.println();
    Serial.println(F("=============================================="));
    Serial.println(F("   ParkTrack 360 — Smart Parking Controller   "));
    Serial.printf( "   Firmware v%s\n", FW_VERSION);
    Serial.println(F("=============================================="));

    // 2. Initialize shared I²C bus (SDA=GPIO21, SCL=GPIO22, 100kHz)
    Wire.begin(PIN_SDA, PIN_SCL, I2C_CLOCK_HZ);
    Serial.println(F("[Init] I2C bus initialized (SDA=21, SCL=22)"));

    // 3. Persistent NVS Storage
    Storage::begin();

    // 4. 16×2 Character LCD display
    Display::begin();

    // 5. 16 slot LEDs via dual PCF8574 expanders
    LEDs::begin();

    // 6. 8 HC-SR04 ultrasonic sensors
    Sensors::begin();

    // 7. Slot occupancy manager (loads baselines from NVS)
    Slots::begin();

    // 8. Barrier gate servos
    Gates::begin();

    // 9. Wi-Fi and WebSocket networking
    Net::begin();

    // 10. Interactive Serial commands
    SerialCmd::begin();

    Serial.println(F("\n[System] All modules initialized and running."));
    Serial.println(F("[System] Type 'help' in Serial Monitor for commands.\n"));
}

void loop() {
    // 1. Process serial commands (non-blocking)
    SerialCmd::update();

    // 2. Ultrasonic sensor reading (reads one sensor per interval)
    // When a full round of 8 sensors completes, update slot logic and LEDs
    bool roundCompleted = Sensors::readNext();
    if (roundCompleted) {
        Slots::update();
        LEDs::update();
    }

    // 3. Servo barrier gate state machine (non-blocking stepping & timing)
    Gates::update();

    // 4. LCD display refresh (updates only on state change)
    Display::update();

    // 5. Network maintenance, WebSocket loop, and periodic heartbeats
    Net::update();
}
