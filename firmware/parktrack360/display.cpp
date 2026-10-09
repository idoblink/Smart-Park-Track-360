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

    static LiquidCrystal_I2C lcd(ADDR_LCD, LCD_COLS, LCD_ROWS);

    // Cache previous display content to avoid redraws
    static char _prevLine0[LCD_COLS + 1] = "";
    static char _prevLine1[LCD_COLS + 1] = "";
    static bool _forceRedraw = true;

    static void writeLine(uint8_t row, const char* text) {
        lcd.setCursor(0, row);
        // Pad to LCD_COLS to clear previous content
        char buf[LCD_COLS + 1];
        snprintf(buf, sizeof(buf), "%-16s", text);
        lcd.print(buf);
    }

    void begin() {
        lcd.init();
        lcd.backlight();
        lcd.clear();
        writeLine(0, " SMART PARKING");
        writeLine(1, "  Starting...");
        _forceRedraw = true;
    }

    void update() {
        char line0[LCD_COLS + 1];
        char line1[LCD_COLS + 1];

        if (!Slots::isCalibrated()) {
            snprintf(line0, sizeof(line0), " SMART PARKING");
            snprintf(line1, sizeof(line1), "  CALIBRATE");
        } else {
            uint8_t occ  = Slots::occupiedCount();
            uint8_t free = Slots::freeCount();

            snprintf(line0, sizeof(line0), " SMART PARKING");

            if (free == 0) {
                snprintf(line1, sizeof(line1), " PARKING FULL");
            } else {
                snprintf(line1, sizeof(line1), "Occ:%-2d Free:%-2d", occ, free);
            }
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
