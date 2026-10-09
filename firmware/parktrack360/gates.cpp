/* =====================================================================
 *  ParkTrack 360 — gates.cpp
 *  Non-blocking servo barrier gate state machine.
 *
 *  State transitions:
 *    CLOSED → OPENING → OPEN (hold timer) → CLOSING → CLOSED
 *
 *  - A second open while OPEN restarts the hold timer.
 *  - An open while CLOSING reverses to OPENING.
 *  - Movement: 2° every 15 ms (~0.7 s for 90°).
 * =====================================================================*/

#include "gates.h"
#include "slots.h"
#include "storage.h"
#include <ESP32Servo.h>

namespace Gates {

    // Per-gate state
    struct GateData {
        Servo       servo;
        uint8_t     pin;
        GateState   state;
        int16_t     currentAngle;   // current position in degrees
        unsigned long stepTimer;    // last step time
        unsigned long holdTimer;    // when hold started
        uint16_t    holdMs;         // how long to hold open
    };

    static GateData _gates[2];
    static uint8_t  _closedAngle = SERVO_CLOSED_DEG;
    static uint8_t  _openAngle   = SERVO_OPEN_DEG;
    static uint16_t _defaultHold = GATE_HOLD_MS;
    static bool     _linkUp = false;

    // --------------- helpers ---------------

    static void writeAngle(GateData& g, int16_t angle) {
        g.currentAngle = angle;
        g.servo.write(angle);
    }

    // --------------- public API ---------------

    void begin() {
        // Load settings from NVS
        _closedAngle = Storage::loadClosedAngle(SERVO_CLOSED_DEG);
        _openAngle   = Storage::loadOpenAngle(SERVO_OPEN_DEG);
        _defaultHold = Storage::loadHoldMs(GATE_HOLD_MS);

        // Configure entry gate
        _gates[GATE_ENTRY].pin = PIN_SERVO_ENTRY;
        _gates[GATE_ENTRY].state = GATE_CLOSED;
        _gates[GATE_ENTRY].currentAngle = _closedAngle;
        _gates[GATE_ENTRY].stepTimer = 0;
        _gates[GATE_ENTRY].holdTimer = 0;
        _gates[GATE_ENTRY].holdMs = _defaultHold;

        // Configure exit gate
        _gates[GATE_EXIT].pin = PIN_SERVO_EXIT;
        _gates[GATE_EXIT].state = GATE_CLOSED;
        _gates[GATE_EXIT].currentAngle = _closedAngle;
        _gates[GATE_EXIT].stepTimer = 0;
        _gates[GATE_EXIT].holdTimer = 0;
        _gates[GATE_EXIT].holdMs = _defaultHold;

        // Attach and set to closed position
        for (uint8_t i = 0; i < 2; i++) {
            _gates[i].servo.setPeriodHertz(50);
            _gates[i].servo.attach(_gates[i].pin, SERVO_MIN_US, SERVO_MAX_US);
            writeAngle(_gates[i], _closedAngle);
        }

        Serial.printf("[Gates] Initialized: closed=%d°, open=%d°, hold=%dms\n",
                      _closedAngle, _openAngle, _defaultHold);
    }

    void update() {
        unsigned long now = millis();

        for (uint8_t i = 0; i < 2; i++) {
            GateData& g = _gates[i];

            switch (g.state) {
                case GATE_OPENING:
                    if (now - g.stepTimer >= SERVO_STEP_MS) {
                        g.stepTimer = now;
                        int16_t target = _openAngle;
                        if (g.currentAngle < target) {
                            int16_t next = g.currentAngle + SERVO_STEP_DEG;
                            if (next > target) next = target;
                            writeAngle(g, next);
                        }
                        if (g.currentAngle >= target) {
                            g.state = GATE_OPEN;
                            g.holdTimer = now;
                            Serial.printf("[Gates] %s gate OPEN (hold %dms)\n",
                                          i == 0 ? "Entry" : "Exit", g.holdMs);
                        }
                    }
                    break;

                case GATE_OPEN:
                    if (now - g.holdTimer >= g.holdMs) {
                        g.state = GATE_CLOSING;
                        g.stepTimer = now;
                        Serial.printf("[Gates] %s gate CLOSING (hold expired)\n",
                                      i == 0 ? "Entry" : "Exit");
                    }
                    break;

                case GATE_CLOSING:
                    if (now - g.stepTimer >= SERVO_STEP_MS) {
                        g.stepTimer = now;
                        int16_t target = _closedAngle;
                        if (g.currentAngle > target) {
                            int16_t next = g.currentAngle - SERVO_STEP_DEG;
                            if (next < target) next = target;
                            writeAngle(g, next);
                        }
                        if (g.currentAngle <= target) {
                            g.state = GATE_CLOSED;
                            Serial.printf("[Gates] %s gate CLOSED\n",
                                          i == 0 ? "Entry" : "Exit");
                        }
                    }
                    break;

                case GATE_CLOSED:
                default:
                    break;
            }
        }
    }

    bool open(GateId gate, uint16_t hold_ms, const char* req_id,
              char* reason, size_t reasonLen) {

        // Clamp hold time
        if (hold_ms < GATE_HOLD_MIN_MS) hold_ms = GATE_HOLD_MIN_MS;
        if (hold_ms > GATE_HOLD_MAX_MS) hold_ms = GATE_HOLD_MAX_MS;

        // Entry gate has additional checks
        if (gate == GATE_ENTRY) {
            if (!Slots::isCalibrated()) {
                snprintf(reason, reasonLen, "uncalibrated");
                Serial.println(F("[Gates] Entry REFUSED: uncalibrated"));
                return false;
            }
            if (Slots::freeCount() == 0) {
                snprintf(reason, reasonLen, "full");
                Serial.println(F("[Gates] Entry REFUSED: parking full"));
                return false;
            }
            if (!_linkUp && strcmp(req_id, "manual") != 0) {
                snprintf(reason, reasonLen, "link");
                Serial.println(F("[Gates] Entry REFUSED: link down"));
                return false;
            }
        }

        GateData& g = _gates[gate];

        if (g.state == GATE_OPENING || g.state == GATE_OPEN) {
            // Already opening/open — restart hold timer
            g.holdMs = hold_ms;
            if (g.state == GATE_OPEN) {
                g.holdTimer = millis();
            }
            Serial.printf("[Gates] %s gate: hold timer restarted (%dms)\n",
                          gate == 0 ? "Entry" : "Exit", hold_ms);
            return true;
        }

        if (g.state == GATE_CLOSING) {
            // Reverse direction
            g.state = GATE_OPENING;
            g.holdMs = hold_ms;
            g.stepTimer = millis();
            Serial.printf("[Gates] %s gate: reversing to OPENING\n",
                          gate == 0 ? "Entry" : "Exit");
            return true;
        }

        // CLOSED → OPENING
        g.state = GATE_OPENING;
        g.holdMs = hold_ms;
        g.stepTimer = millis();
        Serial.printf("[Gates] %s gate: OPENING (hold=%dms)\n",
                      gate == 0 ? "Entry" : "Exit", hold_ms);
        return true;
    }

    void close(GateId gate) {
        GateData& g = _gates[gate];
        if (g.state == GATE_CLOSED) return;

        g.state = GATE_CLOSING;
        g.stepTimer = millis();
        Serial.printf("[Gates] %s gate: CLOSING (manual)\n",
                      gate == 0 ? "Entry" : "Exit");
    }

    GateState getState(GateId gate) {
        return _gates[gate].state;
    }

    const char* getStateStr(GateId gate) {
        switch (_gates[gate].state) {
            case GATE_CLOSED:  return "closed";
            case GATE_OPENING: return "opening";
            case GATE_OPEN:    return "open";
            case GATE_CLOSING: return "closing";
            default:           return "unknown";
        }
    }

    uint8_t getCurrentAngle(GateId gate) {
        return (uint8_t)_gates[gate].currentAngle;
    }

    void setAngles(uint8_t closed, uint8_t open) {
        _closedAngle = closed;
        _openAngle = open;
        Storage::saveClosedAngle(closed);
        Storage::saveOpenAngle(open);
        Serial.printf("[Gates] Angles set: closed=%d°, open=%d°\n", closed, open);
    }

    void setHoldMs(uint16_t ms) {
        if (ms < GATE_HOLD_MIN_MS) ms = GATE_HOLD_MIN_MS;
        if (ms > GATE_HOLD_MAX_MS) ms = GATE_HOLD_MAX_MS;
        _defaultHold = ms;
        Storage::saveHoldMs(ms);
        Serial.printf("[Gates] Hold time set: %dms\n", ms);
    }

    uint8_t getClosedAngle() { return _closedAngle; }
    uint8_t getOpenAngle()   { return _openAngle; }
    uint16_t getHoldMs()     { return _defaultHold; }

    void setLinkUp(bool up) {
        if (_linkUp != up) {
            _linkUp = up;
            Serial.printf("[Gates] Link %s\n", up ? "UP" : "DOWN");
        }
    }

    bool isLinkUp() { return _linkUp; }
}
