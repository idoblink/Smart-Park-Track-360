#pragma once
/* =====================================================================
 *  ParkTrack 360 — leds.h
 *  Slot LEDs via 2× PCF8574 (active-LOW).
 * =====================================================================*/

#include <Arduino.h>
#include "config.h"
#include "slots.h"

namespace LEDs {

    // Call once in setup() — sets both expanders to all-off (0xFF)
    void begin();

    // Refresh LED states from current slot states.
    // Call after Slots::update(). Only writes I²C if the byte changed.
    void update();

    // Write raw byte to ground (floor=0) or first (floor=1) expander.
    // Used by ledtest serial command.
    void writeRaw(uint8_t floor, uint8_t value);

    // Walk all LEDs one by one (blocking, for testing)
    void walkTest();
}
