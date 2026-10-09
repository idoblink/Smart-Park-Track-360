#pragma once
/* =====================================================================
 *  ParkTrack 360 — display.h
 *  16×2 Character LCD display via PCF8574 I²C backpack.
 * =====================================================================*/

#include <Arduino.h>
#include "config.h"

namespace Display {

    // Call once in setup()
    void begin();

    // Refresh the LCD from current state.
    // Only redraws if content changed.  Call in loop().
    void update();

    // Force a specific message (e.g. during calibration).
    // Returns to normal display on next update() with different state.
    void showMessage(const char* line1, const char* line2 = "");
}
