/* =====================================================================
 *  ParkTrack 360 — storage.cpp
 *  NVS (Preferences) wrapper.   Namespace: "pt360"
 *
 *  Keys:
 *    base0..base7  (float)   — calibrated baselines per slot
 *    cal           (bool)    — calibration valid flag
 *    margin        (float)   — occupied margin in cm
 *    closed        (uint8)   — servo closed angle
 *    open          (uint8)   — servo open angle
 *    hold          (uint16)  — gate hold time in ms
 *    ssid          (string)  — Wi-Fi SSID
 *    pass          (string)  — Wi-Fi password
 *    srv_ip        (string)  — server IP address
 *    srv_port      (uint16)  — server port
 * =====================================================================*/

#include "storage.h"
#include <Preferences.h>

namespace Storage {

    static Preferences _prefs;
    static const char* NS = "pt360";

    void begin() {
        _prefs.begin(NS, false);  // read-write
        Serial.println(F("[Storage] NVS namespace 'pt360' opened"));
    }

    // --- Baselines ---
    void saveBaseline(uint8_t slot, float cm) {
        char key[8];
        snprintf(key, sizeof(key), "base%d", slot);
        _prefs.putFloat(key, cm);
    }

    float loadBaseline(uint8_t slot, float defaultVal) {
        char key[8];
        snprintf(key, sizeof(key), "base%d", slot);
        return _prefs.getFloat(key, defaultVal);
    }

    void saveCalibrated(bool cal) {
        _prefs.putBool("cal", cal);
    }

    bool loadCalibrated() {
        return _prefs.getBool("cal", false);
    }

    // --- Margin ---
    void saveMargin(float cm) {
        _prefs.putFloat("margin", cm);
    }

    float loadMargin(float defaultVal) {
        return _prefs.getFloat("margin", defaultVal);
    }

    // --- Gate angles ---
    void saveClosedAngle(uint8_t deg) {
        _prefs.putUChar("closed", deg);
    }

    uint8_t loadClosedAngle(uint8_t defaultVal) {
        return _prefs.getUChar("closed", defaultVal);
    }

    void saveOpenAngle(uint8_t deg) {
        _prefs.putUChar("open", deg);
    }

    uint8_t loadOpenAngle(uint8_t defaultVal) {
        return _prefs.getUChar("open", defaultVal);
    }

    void saveHoldMs(uint16_t ms) {
        _prefs.putUShort("hold", ms);
    }

    uint16_t loadHoldMs(uint16_t defaultVal) {
        return _prefs.getUShort("hold", defaultVal);
    }
}
