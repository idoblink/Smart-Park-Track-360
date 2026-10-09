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

    // --- Network ---
    void   saveSSID(const char* ssid);
    String loadSSID(const char* defaultVal);
    void   savePass(const char* pass);
    String loadPass(const char* defaultVal);
    void   saveServerIP(const char* ip);
    String loadServerIP(const char* defaultVal);
    void   saveServerPort(uint16_t port);
    uint16_t loadServerPort(uint16_t defaultVal);
}
