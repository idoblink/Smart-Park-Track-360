#pragma once
#include <Arduino.h>

/* =====================================================================
 *  ParkTrack 360 — config.h
 *  Central configuration.  Every tunable constant lives here.
 *  Values marked [NVS] can be overridden at run-time via serial
 *  commands and are persisted in ESP32 Non-Volatile Storage.
 * =====================================================================*/

// ---- Firmware version ---------------------------------------------------
#define FW_VERSION  "1.1.0"

// ---- Slot layout --------------------------------------------------------
#define NUM_SLOTS   8
#define NUM_FLOORS  2
#define SLOTS_PER_FLOOR 4

// Slot names in index order: G1 G2 G3 G4 F1 F2 F3 F4
static const char* SLOT_NAMES[NUM_SLOTS] = {
    "G1", "G2", "G3", "G4", "F1", "F2", "F3", "F4"
};
static const char* FLOOR_NAMES[NUM_FLOORS] = {"G", "F"};

// ---- Pins (DO NOT CHANGE without owner approval) ------------------------
static const uint8_t TRIG_PINS[NUM_SLOTS] = {13, 14, 27, 26, 25, 33, 32, 19};
static const uint8_t ECHO_PINS[NUM_SLOTS] = {34, 35, 36, 39, 18,  5, 17, 16};

#define PIN_SDA           21
#define PIN_SCL           22
#define PIN_SERVO_ENTRY   23
#define PIN_SERVO_EXIT    15

// Gate LEDs removed per owner request — GPIO4 and GPIO2 are free.

// ---- I²C addresses (verified by t01_i2c_scan) --------------------------
//  LCD backpack:  0x27 (HW-61 default, no bridges)
//  Ground LEDs:   0x26 (A0 bridged)
//  First LEDs:    0x25 (A1 bridged)
#define ADDR_LCD          0x27
#define ADDR_PCF_GROUND   0x26
#define ADDR_PCF_FIRST    0x25
#define I2C_CLOCK_HZ      100000

// ---- LCD (16×2 character LCD with PCF8574 backpack) ---------------------
#define LCD_COLS  16
#define LCD_ROWS  2

// ---- Sensing ------------------------------------------------------------
#define ECHO_TIMEOUT_US       12000    // ~205 cm max range (prevents timeouts on empty slots)
#define SENSOR_GAP_MS         15       // min gap between consecutive sensors
#define MEDIAN_WINDOW         3        // sliding median window per slot
#define DEBOUNCE_ROUNDS       2        // consecutive rounds before state change (~250 ms)
#define MIN_VALID_CM          1.0f     // readings below this are invalid (allows close range detection)
#define OCCUPIED_THRESHOLD_CM 2.5f     // vehicle / hand at <= 2.5 cm = OCCUPIED
#define OCCUPIED_MARGIN_CM    1.5f     // [NVS] baseline – margin = occupied threshold
#define CAL_ROUNDS            15       // calibration: number of rounds
#define CAL_MAX_SPREAD_CM     6.0f     // max spread allowed during calibration (accommodates normal acoustic jitter)
#define FAULT_ROUNDS          10       // consecutive invalid → fault

// ---- Gates (servo) [NVS overridable] ------------------------------------
#define SERVO_CLOSED_DEG   0
#define SERVO_OPEN_DEG     90
#define SERVO_STEP_DEG     2
#define SERVO_STEP_MS      15          // ms per step → ~0.7 s for 90°
#define SERVO_MIN_US       500
#define SERVO_MAX_US       2400
#define GATE_HOLD_MS       5000        // [NVS] default hold-open time
#define GATE_HOLD_MIN_MS   1000        // server-clamped minimum
#define GATE_HOLD_MAX_MS   15000       // server-clamped maximum

// ---- Host Link (USB Serial 115200 baud) --------------------------------
#define HEARTBEAT_MS        1000       // send state every 1 s
#define LINK_TIMEOUT_MS     5000       // no server heartbeat for 5 s → link lost

