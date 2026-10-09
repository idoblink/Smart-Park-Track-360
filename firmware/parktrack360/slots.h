#pragma once
/* =====================================================================
 *  ParkTrack 360 — slots.h
 *  Slot state management: baseline, debounce, fault detection.
 * =====================================================================*/

#include <Arduino.h>
#include "config.h"

// Slot state enum
enum SlotState : uint8_t {
    SLOT_UNKNOWN      = 0,  // uncalibrated or no data
    SLOT_VACANT       = 1,
    SLOT_OCCUPIED     = 2,
    SLOT_FAULT        = 3
};

namespace Slots {

    // Call once in setup() — loads baselines from NVS
    void begin();

    // Called once per completed sensor round.
    // Reads median distances from Sensors module, applies
    // debounce, and updates slot states.
    void update();

    // Run calibration procedure (blocking, ~3 seconds).
    // Returns true if all slots calibrated successfully.
    // Calls the progress callback with (done, total) during calibration.
    typedef void (*CalProgressCb)(uint8_t done, uint8_t total);
    bool calibrate(CalProgressCb progressCb = nullptr);

    // --- Getters ---
    SlotState getState(uint8_t slot);
    float     getBaseline(uint8_t slot);
    bool      isCalibrated();
    uint8_t   freeCount();       // calibrated + valid + not occupied + not fault
    uint8_t   occupiedCount();
    bool      isFault(uint8_t slot);

    // Get the occupied margin (can be overridden via NVS)
    float     getMargin();

    // Set the occupied margin (and save to NVS)
    void      setMargin(float cm);
}
