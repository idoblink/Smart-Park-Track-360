#pragma once
/* =====================================================================
 *  ParkTrack 360 — storage.h
 *  NVS (Preferences) wrapper for persistent settings.
 *  Namespace: "pt360"
 * =====================================================================*/

#include <Arduino.h>

namespace Storage {

    // Call once in setup()
    void begin();

    // --- Baselines ---
    void  saveBaseline(uint8_t slot, float cm);
    float loadBaseline(uint8_t slot, float defaultVal);
    void  saveCalibrated(bool cal);
    bool  loadCalibrated();

    // --- Margin ---
    void  saveMargin(float cm);
    float loadMargin(float defaultVal);

    // --- Gate angles ---
    void    saveClosedAngle(uint8_t deg);
    uint8_t loadClosedAngle(uint8_t defaultVal);
    void    saveOpenAngle(uint8_t deg);
    uint8_t loadOpenAngle(uint8_t defaultVal);
    void    saveHoldMs(uint16_t ms);
    uint16_t loadHoldMs(uint16_t defaultVal);
}
