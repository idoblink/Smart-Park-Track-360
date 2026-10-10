/* =====================================================================
 *  ParkTrack 360 — comm.cpp
 *  Direct USB Serial Communication (115200 baud).
 *  Communicates directly with the Laptop Host Server over USB cable.
 *
 *  - Sends NDJSON (Newline Delimited JSON) to Serial:
 *      * "hello" on boot / link start
 *      * "state" heartbeat every 1 second
 *      * "cal_progress" / "cal_result"
 *      * "gate_result"
 *  - Receives NDJSON from Serial:
 *      * "hello_ack"
 *      * "hb" (heartbeat from laptop)
 *      * "gate" (open/close entry/exit gate)
 *      * "cmd" (e.g. calibrate)
 *  - Passes human text commands (like 'status', 'help', 'calibrate')
 *    directly to SerialCmd interpreter if not a JSON object!
 * =====================================================================*/

#include "comm.h"
#include "config.h"
#include "slots.h"
#include "gates.h"
#include "sensors.h"
#include "display.h"
#include "serial_cmd.h"
#include <ArduinoJson.h>

namespace Comm {

    static bool _linkUp = false;
    static bool _helloAcked = false;
    static unsigned long _lastHostMsg = 0;
    static unsigned long _lastHeartbeat = 0;
    static bool _calRequested = false;

    // Buffer for reading serial lines
    static char _rxLine[256];
    static uint8_t _rxLen = 0;

    static void handleJsonMessage(const char* payload) {
        JsonDocument doc;
        DeserializationError err = deserializeJson(doc, payload);
        if (err) return;

        const char* t = doc["t"];
        if (!t) return;

        _lastHostMsg = millis();
        if (!_linkUp) {
            _linkUp = true;
            Gates::setLinkUp(true);
        }

        if (strcmp(t, "hello_ack") == 0) {
            _helloAcked = true;
            _linkUp = true;
            Gates::setLinkUp(true);
            Serial.println(F("[Comm] Link active with Host Server via USB Serial"));
        } else if (strcmp(t, "hb") == 0) {
            // Heartbeat received from host
        } else if (strcmp(t, "gate") == 0) {
            const char* gateStr = doc["gate"];
            const char* actionStr = doc["action"];
            uint16_t holdMs = doc["hold_ms"] | 5000;
            const char* reqId = doc["req_id"] | "";

            GateId g = (gateStr && strcmp(gateStr, "entry") == 0) ? GATE_ENTRY : GATE_EXIT;
            bool ok = false;
            char reasonBuf[32] = "";

            if (actionStr && strcmp(actionStr, "open") == 0) {
                ok = Gates::open(g, holdMs, reqId, reasonBuf, sizeof(reasonBuf));
            } else if (actionStr && strcmp(actionStr, "close") == 0) {
                Gates::close(g);
                ok = true;
            }

            JsonDocument resp;
            resp["t"] = "gate_result";
            resp["gate"] = gateStr ? gateStr : "unknown";
            resp["ok"] = ok;
            if (!ok && strlen(reasonBuf) > 0) resp["reason"] = reasonBuf;
            if (reqId && strlen(reqId) > 0) resp["req_id"] = reqId;

            char buf[128];
            serializeJson(resp, buf, sizeof(buf));
            send(buf);

        } else if (strcmp(t, "cmd") == 0) {
            const char* cmdStr = doc["cmd"];
            if (cmdStr && strcmp(cmdStr, "calibrate") == 0) {
                _calRequested = true;
            }
        }
    }

    void handleIncomingLine(const char* line) {
        // Strip leading whitespace
        while (*line == ' ' || *line == '\t') line++;
        if (*line == '\0') return;

        if (line[0] == '{') {
            // JSON message from Python Server
            handleJsonMessage(line);
        } else {
            // Plain text CLI command (help, status, calibrate, etc.)
            SerialCmd::execute(line);
        }
    }

    void begin() {
        _rxLen = 0;
        _rxLine[0] = '\0';
        _linkUp = false;
        _helloAcked = false;
        _lastHostMsg = millis();
        _lastHeartbeat = 0;
        _calRequested = false;

        Serial.println(F("[Comm] USB Serial link active (115200 baud)."));

        // Send initial hello
        JsonDocument doc;
        doc["t"] = "hello";
        doc["fw"] = FW_VERSION;
        doc["conn"] = "usb_serial";
        doc["calibrated"] = Slots::isCalibrated();

        esp_reset_reason_t reason = esp_reset_reason();
        switch (reason) {
            case ESP_RST_POWERON:  doc["reset_reason"] = "power_on"; break;
            case ESP_RST_SW:       doc["reset_reason"] = "software"; break;
            case ESP_RST_PANIC:    doc["reset_reason"] = "panic"; break;
            case ESP_RST_WDT:      doc["reset_reason"] = "watchdog"; break;
            case ESP_RST_BROWNOUT: doc["reset_reason"] = "brownout"; break;
            default:               doc["reset_reason"] = "other"; break;
        }

        char buf[256];
        serializeJson(doc, buf, sizeof(buf));
        send(buf);
    }

    bool send(const char* json) {
        Serial.println(json);
        return true;
    }

    bool isLinkUp() {
        return _linkUp;
    }

    void update() {
        unsigned long now = millis();

        // 1. Read incoming characters from USB Serial
        while (Serial.available()) {
            char c = (char)Serial.read();
            if (c == '\r') continue;
            if (c == '\n') {
                _rxLine[_rxLen] = '\0';
                if (_rxLen > 0) {
                    handleIncomingLine(_rxLine);
                }
                _rxLen = 0;
            } else {
                if (_rxLen < sizeof(_rxLine) - 1) {
                    _rxLine[_rxLen++] = c;
                }
            }
        }

        // 2. Handle pending calibration request
        if (_calRequested) {
            _calRequested = false;
            Display::showMessage("CALIBRATING...", "Keep slots empty");

            bool ok = Slots::calibrate([](uint8_t done, uint8_t total) {
                JsonDocument doc;
                doc["t"] = "cal_progress";
                doc["done"] = done;
                doc["total"] = total;
                char buf[64];
                serializeJson(doc, buf, sizeof(buf));
                send(buf);
            });

            JsonDocument doc;
            doc["t"] = "cal_result";
            doc["ok"] = ok;
            JsonArray baseline = doc["baseline"].to<JsonArray>();
            JsonArray failed = doc["failed"].to<JsonArray>();
            for (uint8_t i = 0; i < NUM_SLOTS; i++) {
                baseline.add(Slots::getBaseline(i));
                if (Slots::getBaseline(i) <= 0.0f) {
                    failed.add(SLOT_NAMES[i]);
                }
            }
            char buf[384];
            serializeJson(doc, buf, sizeof(buf));
            send(buf);
        }

        // 3. Link timeout check (5 seconds timeout)
        if (_linkUp && (now - _lastHostMsg > 5000)) {
            _linkUp = false;
            Gates::setLinkUp(false);
        }

        // 4. Send periodic state update every 1 second
        if (now - _lastHeartbeat >= 1000) {
            _lastHeartbeat = now;

            JsonDocument doc;
            doc["t"] = "state";

            JsonArray slots = doc["slots"].to<JsonArray>();
            JsonArray dist  = doc["dist"].to<JsonArray>();
            JsonArray fault = doc["fault"].to<JsonArray>();

            for (uint8_t i = 0; i < NUM_SLOTS; i++) {
                SlotState s = Slots::getState(i);
                slots.add(s == SLOT_OCCUPIED ? 1 : 0);

                float d = Sensors::getDistance(i);
                if (d >= 0.0f) dist.add(roundf(d * 10.0f) / 10.0f);
                else           dist.add(nullptr);

                fault.add(s == SLOT_FAULT ? 1 : 0);
            }

            doc["entry"]      = Gates::getStateStr(GATE_ENTRY);
            doc["exit"]       = Gates::getStateStr(GATE_EXIT);
            doc["calibrated"] = Slots::isCalibrated();
            doc["free"]       = Slots::freeCount();
            doc["uptime"]     = (uint32_t)(millis() / 1000);

            char buf[512];
            serializeJson(doc, buf, sizeof(buf));
            send(buf);
        }
    }
}
