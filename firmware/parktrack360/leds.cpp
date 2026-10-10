/* =====================================================================
 *  ParkTrack 360 — leds.cpp
 *  Slot LEDs via 2× PCF8574 I²C expanders (active-LOW).
 *
 *  Byte layout per expander (8 pins = 4 slots):
 *    bit 0 = slot 0 green,  bit 1 = slot 0 red
 *    bit 2 = slot 1 green,  bit 3 = slot 1 red
 *    bit 4 = slot 2 green,  bit 5 = slot 2 red
 *    bit 6 = slot 3 green,  bit 7 = slot 3 red
 *
 *  Active-LOW: clear a bit (0) to turn LED ON, set (1) to turn OFF.
 *  Start from 0xFF (all off).
 *
 *  Vacant:  green=ON (0), red=OFF (1)  →  bits: g=0, r=1
 *  Occupied: red=ON (0), green=OFF (1)  →  bits: g=1, r=0
 *  Unknown:  both OFF (1,1)
 *  Fault:    red blinks at ~1 Hz (toggled in update)
 * =====================================================================*/

#include "leds.h"
#include <Wire.h>

namespace LEDs {

    static const uint8_t _addr[2] = { ADDR_PCF_GROUND, ADDR_PCF_FIRST };
    static uint8_t _lastByte[2] = { 0xFF, 0xFF };
    static unsigned long _blinkTimer = 0;
    static bool _blinkState = false;

    // Write one byte to a PCF8574 and return true if ACKed
    static bool writeByte(uint8_t addr, uint8_t val) {
        Wire.beginTransmission(addr);
        Wire.write(val);
        uint8_t err = Wire.endTransmission();
        return (err == 0);
    }

    void begin() {
        _lastByte[0] = 0xFF;
        _lastByte[1] = 0xFF;

        bool groundOk = writeByte(_addr[0], 0xFF);
        bool firstOk  = writeByte(_addr[1], 0xFF);

        if (groundOk) {
            Serial.printf("[LEDs] Ground floor expander detected at 0x%02X.\n", _addr[0]);
        } else {
            Serial.printf("[LEDs] WARNING: Ground floor expander NOT responding at 0x%02X!\n", _addr[0]);
        }

        if (firstOk) {
            Serial.printf("[LEDs] First floor expander detected at 0x%02X.\n", _addr[1]);
        } else {
            Serial.printf("[LEDs] WARNING: First floor expander NOT responding at 0x%02X!\n", _addr[1]);
        }

        _blinkTimer = millis();
        _blinkState = false;
    }

    void update() {
        // Update blink state (~1 Hz)
        unsigned long now = millis();
        if (now - _blinkTimer >= 500) {
            _blinkTimer = now;
            _blinkState = !_blinkState;
        }

        // Build bytes for each floor
        for (uint8_t floor = 0; floor < 2; floor++) {
            uint8_t val = 0xFF;  // start all off

            for (uint8_t s = 0; s < SLOTS_PER_FLOOR; s++) {
                uint8_t slotIdx = floor * SLOTS_PER_FLOOR + s;
                uint8_t greenBit = s * 2;
                uint8_t redBit   = s * 2 + 1;

                SlotState state = Slots::getState(slotIdx);

                switch (state) {
                    case SLOT_VACANT:
                        // Green ON (bit=0), Red OFF (bit=1)
                        val &= ~(1 << greenBit);   // clear green bit → ON
                        // red bit stays 1 → OFF
                        break;

                    case SLOT_OCCUPIED:
                        // Green OFF (bit=1), Red ON (bit=0)
                        val &= ~(1 << redBit);     // clear red bit → ON
                        // green bit stays 1 → OFF
                        break;

                    case SLOT_FAULT:
                        // Red blinks at 1 Hz, green OFF
                        if (_blinkState) {
                            val &= ~(1 << redBit);  // red ON
                        }
                        // else both off
                        break;

                    case SLOT_UNKNOWN:
                    default:
                        // Both OFF (bits stay 1)
                        break;
                }
            }

            // Only write I²C if byte changed (or if blinking faults exist)
            bool hasFault = false;
            for (uint8_t s = 0; s < SLOTS_PER_FLOOR; s++) {
                if (Slots::getState(floor * SLOTS_PER_FLOOR + s) == SLOT_FAULT) {
                    hasFault = true;
                    break;
                }
            }

            if (val != _lastByte[floor] || hasFault) {
                writeByte(_addr[floor], val);
                _lastByte[floor] = val;
            }
        }
    }

    void writeRaw(uint8_t floor, uint8_t value) {
        if (floor >= 2) return;
        bool ok = writeByte(_addr[floor], value);
        if (!ok) {
            Serial.printf("  [NACK] PCF8574 at 0x%02X did not respond!\n", _addr[floor]);
        }
        _lastByte[floor] = value;
    }

    void walkTest() {
        Serial.println(F("\n=== LED Walk Test ==="));

        // Pattern test first
        Serial.println(F("All vacant (0xAA):"));
        writeRaw(0, 0xAA); writeRaw(1, 0xAA); delay(1000);
        Serial.println(F("All occupied (0x55):"));
        writeRaw(0, 0x55); writeRaw(1, 0x55); delay(1000);
        Serial.println(F("All ON (0x00):"));
        writeRaw(0, 0x00); writeRaw(1, 0x00); delay(1000);
        Serial.println(F("All OFF (0xFF):"));
        writeRaw(0, 0xFF); writeRaw(1, 0xFF); delay(1000);

        // Walk each LED
        for (uint8_t floor = 0; floor < 2; floor++) {
            Serial.printf("%s floor:\n", floor == 0 ? "Ground" : "First");
            for (uint8_t pin = 0; pin < 8; pin++) {
                uint8_t val = 0xFF & ~(1 << pin);
                writeRaw(floor, val);
                Serial.printf("  P%d ON [byte=0x%02X]\n", pin, val);
                delay(500);
                writeRaw(floor, 0xFF);
            }
        }

        Serial.println(F("=== LED Walk Test Complete ===\n"));
    }
}
