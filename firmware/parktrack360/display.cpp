/* =====================================================================
 *  ParkTrack 360 — display.cpp
 *  16×2 Character LCD via PCF8574 I²C backpack.
 *
 *  Layout:
 *    Line 0: "SMART PARKING" or "  CALIBRATE"
 *    Line 1: "Occ:N  Free:M" or "  PARKING FULL"
 *
 *  Uses the LiquidCrystal_I2C library by Frank de Brabander.
 * =====================================================================*/

#include "display.h"
#include "slots.h"
#include <LiquidCrystal_I2C.h>

namespace Display {

    static LiquidCrystal_I2C* _lcd = nullptr;
    static uint8_t _lcdAddr = ADDR_LCD;

    // Cache previous display content to avoid redraws
    static char _prevLine0[LCD_COLS + 1] = "";
    static char _prevLine1[LCD_COLS + 1] = "";
    static bool _forceRedraw = true;

    static void writeLine(uint8_t row, const char* text) {
        if (!_lcd) return;
        _lcd->setCursor(0, row);
        // Pad to LCD_COLS to clear previous content
        char buf[LCD_COLS + 1];
        snprintf(buf, sizeof(buf), "%-16s", text);
        _lcd->print(buf);
    }

    void begin() {
        // Probe whether LCD is at 0x27 (PCF8574T) or 0x3F (PCF8574AT)
        _lcdAddr = ADDR_LCD;
        Wire.beginTransmission(0x27);
        if (Wire.endTransmission() != 0) {
            // 0x27 did not answer, probe 0x3F
            Wire.beginTransmission(0x3F);
            if (Wire.endTransmission() == 0) {
                _lcdAddr = 0x3F;
                Serial.println(F("[Display] LCD auto-detected at address 0x3F (PCF8574A chip)!"));
            } else {
                Serial.println(F("[Display] WARNING: LCD not responding at 0x27 or 0x3F! Check SDA/SCL wiring."));
            }
        } else {
            Serial.println(F("[Display] LCD detected at default address 0x27."));
        }

        if (_lcd) delete _lcd;
        _lcd = new LiquidCrystal_I2C(_lcdAddr, LCD_COLS, LCD_ROWS);
        _lcd->init();
        _lcd->backlight();
        _lcd->clear();
        writeLine(0, " SMART PARKING");
        writeLine(1, "  Starting...");
        _forceRedraw = true;
    }

    void update() {
        char line0[LCD_COLS + 1];
        char line1[LCD_COLS + 1];

        uint8_t occ  = Slots::occupiedCount();
        uint8_t free = Slots::freeCount();

        snprintf(line0, sizeof(line0), " SMART PARKING");

        if (free == 0 && occ > 0) {
            snprintf(line1, sizeof(line1), " PARKING FULL");
        } else {
            snprintf(line1, sizeof(line1), "Occ:%-2d Free:%-2d", occ, free);
        }

        // Only redraw if content changed
        if (_forceRedraw ||
            strcmp(line0, _prevLine0) != 0 ||
            strcmp(line1, _prevLine1) != 0) {

            writeLine(0, line0);
            writeLine(1, line1);
            strncpy(_prevLine0, line0, LCD_COLS);
            strncpy(_prevLine1, line1, LCD_COLS);
            _prevLine0[LCD_COLS] = '\0';
            _prevLine1[LCD_COLS] = '\0';
            _forceRedraw = false;
        }
    }

    void showMessage(const char* line1, const char* line2) {
        writeLine(0, line1);
        writeLine(1, line2);
        strncpy(_prevLine0, line1, LCD_COLS);
        strncpy(_prevLine1, line2, LCD_COLS);
        _prevLine0[LCD_COLS] = '\0';
        _prevLine1[LCD_COLS] = '\0';
    }
}
