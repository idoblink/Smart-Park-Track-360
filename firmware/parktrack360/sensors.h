#pragma once
/* =====================================================================
 *  ParkTrack 360 — sensors.h
 *  HC-SR04 ultrasonic sensor driver.
 *  Reads 8 sensors sequentially, one per call to readNext().
 * =====================================================================*/

#include <Arduino.h>
#include "config.h"

namespace Sensors {

    // Call once in setup()
    void begin();

    // Read the next sensor in round-robin order (blocks ≤8 ms).
    // Returns true when a full round (all 8 sensors) is complete.
    bool readNext();

    // Latest distance for slot i (median-filtered, cm).  -1.0 = invalid.
    float getDistance(uint8_t slot);

    // Raw latest single reading (no median), for debugging.
    float getRawDistance(uint8_t slot);

    // Current sensor index (0-7) — the one that will be read next.
    uint8_t currentIndex();
}
