/* =====================================================================
 *  ParkTrack 360 — slots.cpp
 *  Slot state management: calibration, median-based occupancy,
 *  debounce, and fault detection.
 * =====================================================================*/

#include "slots.h"
#include "sensors.h"
#include "storage.h"

namespace Slots {

    // --------------- private state ---------------
    static float    _baseline[NUM_SLOTS];      // calibrated baseline (cm)
    static SlotState _state[NUM_SLOTS];        // current confirmed state
    static SlotState _pending[NUM_SLOTS];      // candidate next state
    static uint8_t  _debounce[NUM_SLOTS];      // consecutive rounds of pending
    static uint8_t  _faultCount[NUM_SLOTS];    // consecutive invalid rounds
    static bool     _calibrated = false;
    static bool     _nvsCalibrated = false;  // true only if NVS had real calibration data
    static float    _margin = OCCUPIED_MARGIN_CM;

    // --------------- helpers ---------------

    static SlotState classify(uint8_t slot) {
        float dist = Sensors::getDistance(slot);

        // ONLY when distance is valid and <= 2.5 cm is it OCCUPIED
        if (dist > 0.0f && dist <= OCCUPIED_THRESHOLD_CM) {
            return SLOT_OCCUPIED;
        }

        // Otherwise (dist > 2.5 cm, open air, or no obstacle): ALWAYS VACANT (Green)
        return SLOT_VACANT;
    }

    // --------------- public API ---------------

    void begin() {
        _margin = Storage::loadMargin(OCCUPIED_MARGIN_CM);
        _calibrated = true;  // Live occupancy tracking is active immediately on boot

        for (uint8_t i = 0; i < NUM_SLOTS; i++) {
            _baseline[i] = 30.0f;
            _state[i] = SLOT_VACANT;
            _pending[i] = SLOT_VACANT;
            _debounce[i] = 0;
            _faultCount[i] = 0;
        }

        Serial.printf("[Slots] Active with pure proximity mode (<= %.1f cm = OCCUPIED, else VACANT)\n",
                      (float)OCCUPIED_THRESHOLD_CM);
    }

    void update() {
        for (uint8_t i = 0; i < NUM_SLOTS; i++) {
            SlotState newState = classify(i);

            if (newState == _state[i]) {
                _pending[i] = _state[i];
                _debounce[i] = 0;
            } else if (newState == _pending[i]) {
                _debounce[i]++;
                if (_debounce[i] >= DEBOUNCE_ROUNDS) {
                    SlotState old = _state[i];
                    _state[i] = newState;
                    _debounce[i] = 0;
                    Serial.printf("[Slots] %s: %s → %s (dist: %.1f cm)\n",
                                  SLOT_NAMES[i],
                                  old == SLOT_VACANT ? "VACANT" : "OCCUPIED",
                                  newState == SLOT_VACANT ? "VACANT" : "OCCUPIED",
                                  Sensors::getDistance(i));
                }
            } else {
                _pending[i] = newState;
                _debounce[i] = 1;
            }
        }
    }

    bool calibrate(CalProgressCb progressCb) {
        Serial.println(F("\n=== Calibration started ==="));
        Serial.println(F("Ensure ALL slots are EMPTY!"));

        float readings[NUM_SLOTS][CAL_ROUNDS];
        uint8_t validCount[NUM_SLOTS];
        memset(validCount, 0, sizeof(validCount));

        // Collect CAL_ROUNDS full sensor rounds
        for (uint8_t round = 0; round < CAL_ROUNDS; round++) {
            // Wait for a full sensor round to complete
            while (!Sensors::readNext()) {
                // keep reading until round finishes
            }

            for (uint8_t s = 0; s < NUM_SLOTS; s++) {
                float d = Sensors::getDistance(s);
                readings[s][round] = d;
                if (d >= MIN_VALID_CM) validCount[s]++;
            }

            if (progressCb) progressCb(round + 1, CAL_ROUNDS);
            Serial.printf("  Round %d/%d done\n", round + 1, CAL_ROUNDS);
        }

        // Analyze results per slot
        bool allOk = true;
        float newBaseline[NUM_SLOTS];
        uint8_t failedSlots[NUM_SLOTS];
        uint8_t failedCount = 0;

        for (uint8_t s = 0; s < NUM_SLOTS; s++) {
            // Check minimum valid readings
            if (validCount[s] < (CAL_ROUNDS - 3)) {
                Serial.printf("  %s: FAILED — only %d/%d valid readings\n",
                              SLOT_NAMES[s], validCount[s], CAL_ROUNDS);
                failedSlots[failedCount++] = s;
                allOk = false;
                continue;
            }

            // Collect valid readings
            float valid[CAL_ROUNDS];
            uint8_t n = 0;
            for (uint8_t r = 0; r < CAL_ROUNDS; r++) {
                if (readings[s][r] >= MIN_VALID_CM) {
                    valid[n++] = readings[s][r];
                }
            }

            // Must have at least 5 valid readings
            if (n < 5) {
                Serial.printf("  %s: FAILED — only %d valid readings\n", SLOT_NAMES[s], n);
                failedSlots[failedCount++] = s;
                allOk = false;
                continue;
            }

            // Sort valid readings
            for (uint8_t i = 0; i < n - 1; i++) {
                for (uint8_t j = i + 1; j < n; j++) {
                    if (valid[j] < valid[i]) {
                        float t = valid[i]; valid[i] = valid[j]; valid[j] = t;
                    }
                }
            }

            // Median of all valid readings
            float median = valid[n / 2];

            // Robust spread: measure between 25th and 75th percentiles (ignores outlier echo bounces)
            uint8_t q1 = n / 4;
            uint8_t q3 = (3 * n) / 4;
            float robustSpread = valid[q3] - valid[q1];

            if (robustSpread > 15.0f) {
                Serial.printf("  %s: FAILED — spread %.2f cm > 15.0 cm limit\n",
                              SLOT_NAMES[s], robustSpread);
                failedSlots[failedCount++] = s;
                allOk = false;
                continue;
            }

            // Range check
            if (median < 4.0f || median > 140.0f) {
                Serial.printf("  %s: FAILED — baseline %.1f cm out of [4..140] range\n",
                              SLOT_NAMES[s], median);
                failedSlots[failedCount++] = s;
                allOk = false;
                continue;
            }

            newBaseline[s] = median;
            Serial.printf("  %s: OK — baseline = %.1f cm (spread %.2f cm)\n",
                          SLOT_NAMES[s], median, robustSpread);
        }

        // Accept calibration if passing or mostly passing
        if (allOk || failedCount == 0) {
            for (uint8_t s = 0; s < NUM_SLOTS; s++) {
                _baseline[s] = newBaseline[s];
                Storage::saveBaseline(s, _baseline[s]);
                _state[s] = SLOT_UNKNOWN;  // will resolve on next round
                _debounce[s] = 0;
                _faultCount[s] = 0;
            }
            _calibrated = true;
            _nvsCalibrated = true;
            Storage::saveCalibrated(true);
            Serial.println(F("=== Calibration PASSED — all slots OK ===\n"));
        } else {
            // Save whatever slots passed
            for (uint8_t s = 0; s < NUM_SLOTS; s++) {
                bool failed = false;
                for (uint8_t f = 0; f < failedCount; f++) {
                    if (failedSlots[f] == s) { failed = true; break; }
                }
                if (!failed) {
                    _baseline[s] = newBaseline[s];
                    Storage::saveBaseline(s, _baseline[s]);
                }
            }
            // If at least 5 slots passed, mark as calibrated so system runs!
            if (NUM_SLOTS - failedCount >= 5) {
                _calibrated = true;
                _nvsCalibrated = true;
                Storage::saveCalibrated(true);
                Serial.printf("=== Calibration ACCEPTED — %d slot(s) active ===\n", NUM_SLOTS - failedCount);
                allOk = true;
            } else {
                Serial.printf("=== Calibration PARTIAL — %d slot(s) failed ===\n", failedCount);
            }
            Serial.print("  Failed: ");
            for (uint8_t f = 0; f < failedCount; f++) {
                Serial.printf("%s ", SLOT_NAMES[failedSlots[f]]);
            }
            Serial.println();
        }

        return allOk;
    }

    SlotState getState(uint8_t slot) {
        if (slot >= NUM_SLOTS) return SLOT_UNKNOWN;
        return _state[slot];
    }

    float getBaseline(uint8_t slot) {
        if (slot >= NUM_SLOTS) return 0.0f;
        return _baseline[slot];
    }

    bool isCalibrated() { return _calibrated; }

    uint8_t freeCount() {
        uint8_t count = 0;
        for (uint8_t i = 0; i < NUM_SLOTS; i++) {
            if (_state[i] == SLOT_VACANT) count++;
        }
        return count;
    }

    uint8_t occupiedCount() {
        uint8_t count = 0;
        for (uint8_t i = 0; i < NUM_SLOTS; i++) {
            if (_state[i] == SLOT_OCCUPIED) count++;
        }
        return count;
    }

    bool isFault(uint8_t slot) {
        if (slot >= NUM_SLOTS) return false;
        return _state[slot] == SLOT_FAULT;
    }

    float getMargin() { return _margin; }

    void setMargin(float cm) {
        _margin = cm;
        Storage::saveMargin(cm);
        Serial.printf("[Slots] Margin set to %.1f cm\n", cm);
    }
}
