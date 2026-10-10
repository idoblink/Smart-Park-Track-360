#pragma once
/* =====================================================================
 *  ParkTrack 360 — serial_cmd.h
 *  Serial command interpreter for hardware testing, calibration,
 *  network setup, and runtime tuning (115200 baud).
 * =====================================================================*/

#include <Arduino.h>

namespace SerialCmd {

    // Call once in setup()
    void begin();

    // Call in loop() to read and process serial input non-blockingly
    void update();

    // Execute a command string directly
    void execute(const char* cmd);

    // Print help text
    void printHelp();

    // Print current full system status
    void printStatus();
}
