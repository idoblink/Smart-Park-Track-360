/* =====================================================================
 *  ParkTrack 360 — sensors.cpp
 *  HC-SR04 sequential reader with median-of-3 sliding window.
 *
 *  One sensor is read per call to readNext().  A full round
 *  (all 8) completes in ~130-190 ms.  Each sensor naturally gets
 *  ≥ 15 ms gap because the round takes much longer.
 * =====================================================================*/

#include "sensors.h"

namespace Sensors {

    // --------------- private state ---------------
    static float _raw[NUM_SLOTS];                    // latest single reading
    static float _window[NUM_SLOTS][MEDIAN_WINDOW];  // sliding window
    static uint8_t _wIdx[NUM_SLOTS];                 // write pointer per slot
    static uint8_t _wCount[NUM_SLOTS];               // # valid entries in window
    static float _median[NUM_SLOTS];                 // computed median
    static uint8_t _nextSlot = 0;
    static unsigned long _lastReadMs = 0;

    // --------------- helpers ---------------

    // Return median of up to 3 values.  Invalid values (< 0) are excluded.
    static float computeMedian(uint8_t slot) {
        float valid[MEDIAN_WINDOW];
        uint8_t n = 0;
        for (uint8_t i = 0; i < MEDIAN_WINDOW; i++) {
            if (_window[slot][i] >= MIN_VALID_CM) {
                valid[n++] = _window[slot][i];
            }
        }
        if (n == 0) return -1.0f;
        if (n == 1) return valid[0];
        // simple sort for 2-3 values
        if (n == 2) return (valid[0] + valid[1]) / 2.0f;
        // n == 3: sort and pick middle
        if (valid[0] > valid[1]) { float t = valid[0]; valid[0] = valid[1]; valid[1] = t; }
        if (valid[1] > valid[2]) { float t = valid[1]; valid[1] = valid[2]; valid[2] = t; }
        if (valid[0] > valid[1]) { float t = valid[0]; valid[0] = valid[1]; valid[1] = t; }
        return valid[1];
    }

    // Trigger and read one HC-SR04.  Returns distance in cm, or -1 on timeout.
    static float readOneSensor(uint8_t slot) {
        uint8_t trig = TRIG_PINS[slot];
        uint8_t echo = ECHO_PINS[slot];

        // Send 10 µs trigger pulse
        digitalWrite(trig, LOW);
        delayMicroseconds(2);
        digitalWrite(trig, HIGH);
        delayMicroseconds(10);
        digitalWrite(trig, LOW);

        // Measure echo pulse duration
        unsigned long dur = pulseIn(echo, HIGH, ECHO_TIMEOUT_US);
        if (dur == 0) return -1.0f;  // timeout

        float cm = (float)dur / 58.3f;
        if (cm < MIN_VALID_CM) return -1.0f;  // too close / dead zone
        return cm;
    }

    // --------------- public API ---------------

    void begin() {
        for (uint8_t i = 0; i < NUM_SLOTS; i++) {
            pinMode(TRIG_PINS[i], OUTPUT);
            digitalWrite(TRIG_PINS[i], LOW);
            // ECHO pins: input (no pull-up on 34/35/36/39)
            pinMode(ECHO_PINS[i], INPUT);

            _raw[i] = -1.0f;
            _median[i] = -1.0f;
            _wIdx[i] = 0;
            _wCount[i] = 0;
            for (uint8_t w = 0; w < MEDIAN_WINDOW; w++) {
                _window[i][w] = -1.0f;
            }
        }
        _nextSlot = 0;
        _lastReadMs = 0;
    }

    bool readNext() {
        // Enforce minimum gap between reads
        unsigned long now = millis();
        if (now - _lastReadMs < SENSOR_GAP_MS) return false;

        uint8_t s = _nextSlot;
        float d = readOneSensor(s);
        _raw[s] = d;

        // Push into sliding window
        _window[s][_wIdx[s]] = d;
        _wIdx[s] = (_wIdx[s] + 1) % MEDIAN_WINDOW;
        if (_wCount[s] < MEDIAN_WINDOW) _wCount[s]++;

        // Recompute median
        _median[s] = computeMedian(s);

        _lastReadMs = millis();
        _nextSlot = (_nextSlot + 1) % NUM_SLOTS;

        // Return true when we just completed a full round (read slot 7)
        return (s == NUM_SLOTS - 1);
    }

    float getDistance(uint8_t slot) {
        if (slot >= NUM_SLOTS) return -1.0f;
        return _median[slot];
    }

    float getRawDistance(uint8_t slot) {
        if (slot >= NUM_SLOTS) return -1.0f;
        return _raw[slot];
    }

    uint8_t currentIndex() {
        return _nextSlot;
    }
}
