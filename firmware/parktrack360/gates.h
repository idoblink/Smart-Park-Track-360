#pragma once
/* =====================================================================
 *  ParkTrack 360 — gates.h
 *  Servo barrier gate state machine (non-blocking, gradual movement).
 * =====================================================================*/

#include <Arduino.h>
#include "config.h"

// Gate identifiers
enum GateId : uint8_t {
    GATE_ENTRY = 0,
    GATE_EXIT  = 1
};

// Gate state machine states
enum GateState : uint8_t {
    GATE_CLOSED  = 0,
    GATE_OPENING = 1,
    GATE_OPEN    = 2,
    GATE_CLOSING = 3
};

namespace Gates {

    // Call once in setup().
    // Attaches servos and sets them to closed position.
    void begin();

    // Non-blocking update.  Call every loop iteration.
    // Steps servos, manages hold timers, etc.
    void update();

    // Request to open a gate.  Returns false if refused
    // (full, uncalibrated, link lost for entry gate).
    // reason is filled with the refusal reason string (if refused).
    // hold_ms: how long to hold open (clamped to min/max).
    // req_id: optional request ID for gate_result messages.
    bool open(GateId gate, uint16_t hold_ms, const char* req_id,
              char* reason, size_t reasonLen);

    // Request to close a gate immediately (goes through CLOSING).
    void close(GateId gate);

    // --- Getters ---
    GateState getState(GateId gate);
    const char* getStateStr(GateId gate);
    uint8_t getCurrentAngle(GateId gate);

    // Set servo angles (and save to NVS)
    void setAngles(uint8_t closed, uint8_t open);

    // Set hold time (and save to NVS)
    void setHoldMs(uint16_t ms);

    // Get current settings
    uint8_t getClosedAngle();
    uint8_t getOpenAngle();
    uint16_t getHoldMs();

    // Set link status (gates won't open entry if link is lost)
    void setLinkUp(bool up);
    bool isLinkUp();
}
