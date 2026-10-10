#pragma once
/* =====================================================================
 *  ParkTrack 360 — comm.h
 *  Direct USB Serial Communication Interface (115200 baud).
 *  Communicates directly with the Laptop Host Server over USB cable.
 *  Zero Wi-Fi, zero network dependencies, 100% autonomous wired link.
 * =====================================================================*/

#include <Arduino.h>

namespace Comm {

    // Initialize USB Serial interface (call in setup)
    void begin();

    // Process serial characters, send periodic state updates, and handle commands (call in loop)
    void update();

    // Check if host communication link is active
    bool isLinkUp();

    // Send a JSON string line directly to the laptop server
    bool send(const char* json);
}
