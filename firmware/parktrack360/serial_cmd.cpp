/* =====================================================================
 *  ParkTrack 360 — serial_cmd.cpp
 *  Interactive serial command interpreter (115200 baud).
 * =====================================================================*/

#include "serial_cmd.h"
#include "config.h"
#include "slots.h"
#include "sensors.h"
#include "gates.h"
#include "leds.h"
#include "display.h"
#include "net.h"
#include "storage.h"
#include <Wire.h>

namespace SerialCmd {

    static char _rxBuffer[128];
    static uint8_t _rxIndex = 0;

    void begin() {
        _rxIndex = 0;
        _rxBuffer[0] = '\0';
    }

    void printHelp() {
        Serial.println(F("\n================ ParkTrack 360 Commands ================"));
        Serial.println(F("  help                      - Show this command list"));
        Serial.println(F("  status                    - Print slots, distances, gates, link, status"));
        Serial.println(F("  calibrate                 - Run baseline calibration (all slots empty)"));
        Serial.println(F("  gate entry open           - Open entry gate (manual hold)"));
        Serial.println(F("  gate entry close          - Close entry gate immediately"));
        Serial.println(F("  gate exit open            - Open exit gate (manual hold)"));
        Serial.println(F("  gate exit close           - Close exit gate immediately"));
        Serial.println(F("  wifi <ssid> <password>    - Save Wi-Fi credentials to NVS and reconnect"));
        Serial.println(F("  server <ip> <port>        - Save server address to NVS and reconnect"));
        Serial.println(F("  margin <cm>               - Set occupied detection margin (e.g. margin 1.5)"));
        Serial.println(F("  angles <closed> <open>    - Set servo angles in degrees (e.g. angles 0 90)"));
        Serial.println(F("  hold <ms>                 - Set gate hold time in ms (e.g. hold 5000)"));
        Serial.println(F("  scan                      - Scan I2C bus for connected modules"));
        Serial.println(F("  ledtest                   - Step through all 16 slot LEDs one by one"));
        Serial.println(F("  reboot                    - Restart the ESP32"));
        Serial.println(F("========================================================\n"));
    }

    void printStatus() {
        Serial.println(F("\n================ ParkTrack 360 System Status ================"));
        Serial.printf("Firmware: %s | Uptime: %lu s | Calibrated: %s\n",
                      FW_VERSION, millis() / 1000,
                      Slots::isCalibrated() ? "YES" : "NO (run 'calibrate')");
        Serial.printf("Free Slots: %d / %d  |  Occupied: %d  |  Margin: %.1f cm\n",
                      Slots::freeCount(), NUM_SLOTS, Slots::occupiedCount(), Slots::getMargin());

        Serial.println(F("\n--- Slot Status ---"));
        Serial.println(F("Slot  State       Distance    Raw       Baseline  Fault"));
        Serial.println(F("----  ----------  ----------  --------  --------  -----"));
        for (uint8_t i = 0; i < NUM_SLOTS; i++) {
            SlotState st = Slots::getState(i);
            const char* stStr = "UNKNOWN ";
            if (st == SLOT_VACANT)   stStr = "VACANT  ";
            if (st == SLOT_OCCUPIED) stStr = "OCCUPIED";
            if (st == SLOT_FAULT)    stStr = "FAULT   ";

            float dist = Sensors::getDistance(i);
            float raw  = Sensors::getRawDistance(i);
            float base = Slots::getBaseline(i);

            char distStr[16], rawStr[16], baseStr[16];
            if (dist >= 0) snprintf(distStr, sizeof(distStr), "%5.1f cm", dist);
            else           snprintf(distStr, sizeof(distStr), "   --   ");

            if (raw >= 0)  snprintf(rawStr, sizeof(rawStr), "%5.1f cm", raw);
            else           snprintf(rawStr, sizeof(rawStr), "   --   ");

            if (base > 0)  snprintf(baseStr, sizeof(baseStr), "%5.1f cm", base);
            else           snprintf(baseStr, sizeof(baseStr), "   --   ");

            Serial.printf("%-4s  %-10s  %-10s  %-8s  %-8s  %s\n",
                          SLOT_NAMES[i], stStr, distStr, rawStr, baseStr,
                          Slots::isFault(i) ? "YES" : "no");
        }

        Serial.println(F("\n--- Gates ---"));
        Serial.printf("Entry Gate: %-7s (angle: %3d°) | Exit Gate: %-7s (angle: %3d°)\n",
                      Gates::getStateStr(GATE_ENTRY), Gates::getCurrentAngle(GATE_ENTRY),
                      Gates::getStateStr(GATE_EXIT),  Gates::getCurrentAngle(GATE_EXIT));
        Serial.printf("Settings:   Closed=%d°, Open=%d°, Hold=%d ms\n",
                      Gates::getClosedAngle(), Gates::getOpenAngle(), Gates::getHoldMs());

        Serial.println(F("\n--- Network ---"));
        Serial.printf("Wi-Fi:   %s (IP: %s)\n",
                      Net::isWifiConnected() ? "CONNECTED" : "DISCONNECTED",
                      Net::isWifiConnected() ? Net::getIP().c_str() : "0.0.0.0");
        Serial.printf("Server:  %s\n", Net::isLinkUp() ? "LINK UP" : "LINK DOWN");
        Serial.println(F("============================================================\n"));
    }

    static void executeScan() {
        Serial.println(F("\n[I2C] Scanning I2C bus (SDA=21, SCL=22)..."));
        uint8_t count = 0;
        for (uint8_t addr = 1; addr < 127; addr++) {
            Wire.beginTransmission(addr);
            if (Wire.endTransmission() == 0) {
                Serial.printf("  Found device at address 0x%02X", addr);
                if (addr == ADDR_LCD)         Serial.print(F(" (16x2 LCD Backpack)"));
                else if (addr == ADDR_PCF_GROUND) Serial.print(F(" (Ground Floor LEDs)"));
                else if (addr == ADDR_PCF_FIRST)  Serial.print(F(" (First Floor LEDs)"));
                Serial.println();
                count++;
            }
        }
        Serial.printf("[I2C] Scan complete. %d device(s) found.\n\n", count);
    }

    static void handleCommand(char* cmd) {
        // Strip leading whitespace
        while (*cmd == ' ' || *cmd == '\t') cmd++;
        if (*cmd == '\0') return;

        // Strip trailing whitespace / cr / lf
        int len = strlen(cmd);
        while (len > 0 && (cmd[len - 1] == ' ' || cmd[len - 1] == '\r' || cmd[len - 1] == '\n')) {
            cmd[--len] = '\0';
        }

        if (strcasecmp(cmd, "help") == 0) {
            printHelp();

        } else if (strcasecmp(cmd, "status") == 0) {
            printStatus();

        } else if (strcasecmp(cmd, "calibrate") == 0) {
            Serial.println(F("\n[Calibration] Starting calibration. Keep all 8 slots empty!"));
            Display::showMessage("CALIBRATING...", "Keep slots empty");
            bool ok = Slots::calibrate([](uint8_t done, uint8_t total) {
                char line2[17];
                snprintf(line2, sizeof(line2), "Round %d/%d", done, total);
                Display::showMessage("CALIBRATING...", line2);
            });
            if (ok) {
                Serial.println(F("[Calibration] Completed successfully."));
                Display::showMessage("CALIBRATION OK", "All 8 slots set");
            } else {
                Serial.println(F("[Calibration] FAILED for one or more slots. Check sensor alignment/wiring."));
                Display::showMessage("CALIB FAILED", "Check Serial");
            }

        } else if (strncasecmp(cmd, "gate", 4) == 0) {
            char gName[16] = "";
            char action[16] = "";
            if (sscanf(cmd, "%*s %15s %15s", gName, action) == 2) {
                GateId gid = (strcasecmp(gName, "entry") == 0) ? GATE_ENTRY : GATE_EXIT;
                if (strcasecmp(action, "open") == 0) {
                    char reason[32] = "";
                    bool ok = Gates::open(gid, Gates::getHoldMs(), "manual", reason, sizeof(reason));
                    if (!ok) {
                        Serial.printf("[Gates] Manual open REFUSED: %s\n", reason);
                    } else {
                        Serial.printf("[Gates] Opening %s gate...\n", (gid == GATE_ENTRY) ? "entry" : "exit");
                    }
                } else if (strcasecmp(action, "close") == 0) {
                    Gates::close(gid);
                    Serial.printf("[Gates] Closing %s gate...\n", (gid == GATE_ENTRY) ? "entry" : "exit");
                } else {
                    Serial.println(F("[Gates] Invalid action. Use 'open' or 'close'."));
                }
            } else {
                Serial.println(F("Usage: gate <entry|exit> <open|close>"));
            }

        } else if (strncasecmp(cmd, "wifi", 4) == 0) {
            char ssid[64] = "";
            char pass[64] = "";
            if (sscanf(cmd, "%*s %63s %63s", ssid, pass) == 2) {
                Net::setWifi(ssid, pass);
            } else {
                Serial.println(F("Usage: wifi <ssid> <password>"));
            }

        } else if (strncasecmp(cmd, "server", 6) == 0) {
            char ip[64] = "";
            int port = 0;
            if (sscanf(cmd, "%*s %63s %d", ip, &port) == 2 && port > 0 && port <= 65535) {
                Net::setServer(ip, (uint16_t)port);
            } else {
                Serial.println(F("Usage: server <ip> <port>"));
            }

        } else if (strncasecmp(cmd, "margin", 6) == 0) {
            float cm = 0.0f;
            if (sscanf(cmd, "%*s %f", &cm) == 1 && cm > 0.0f) {
                Slots::setMargin(cm);
                Serial.printf("[Config] Margin updated to %.2f cm\n", cm);
            } else {
                Serial.println(F("Usage: margin <cm> (e.g. margin 1.5)"));
            }

        } else if (strncasecmp(cmd, "angles", 6) == 0) {
            int closed = 0, open = 0;
            if (sscanf(cmd, "%*s %d %d", &closed, &open) == 2 &&
                closed >= 0 && closed <= 180 && open >= 0 && open <= 180) {
                Gates::setAngles((uint8_t)closed, (uint8_t)open);
                Serial.printf("[Config] Gate angles updated: closed=%d°, open=%d°\n", closed, open);
            } else {
                Serial.println(F("Usage: angles <closed> <open> (e.g. angles 0 90)"));
            }

        } else if (strncasecmp(cmd, "hold", 4) == 0) {
            int ms = 0;
            if (sscanf(cmd, "%*s %d", &ms) == 1 && ms >= 500 && ms <= 30000) {
                Gates::setHoldMs((uint16_t)ms);
                Serial.printf("[Config] Gate hold time updated to %d ms\n", ms);
            } else {
                Serial.println(F("Usage: hold <ms> (e.g. hold 5000)"));
            }

        } else if (strcasecmp(cmd, "scan") == 0) {
            executeScan();

        } else if (strcasecmp(cmd, "ledtest") == 0) {
            LEDs::walkTest();

        } else if (strcasecmp(cmd, "reboot") == 0) {
            Serial.println(F("[System] Rebooting ESP32..."));
            delay(200);
            ESP.restart();

        } else {
            Serial.printf("Unknown command: '%s'. Type 'help' for command list.\n", cmd);
        }
    }

    void update() {
        while (Serial.available() > 0) {
            char c = (char)Serial.read();
            if (c == '\r' || c == '\n') {
                if (_rxIndex > 0) {
                    _rxBuffer[_rxIndex] = '\0';
                    handleCommand(_rxBuffer);
                    _rxIndex = 0;
                }
            } else if (_rxIndex < sizeof(_rxBuffer) - 1) {
                _rxBuffer[_rxIndex++] = c;
            }
        }
    }
}
