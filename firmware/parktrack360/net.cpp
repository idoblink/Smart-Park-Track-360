/* =====================================================================
 *  ParkTrack 360 — net.cpp
 *  Wi-Fi + WebSocket client.
 *
 *  - Connects to Wi-Fi in STA mode (non-blocking).
 *  - Opens a WebSocket to ws://<server_ip>:<port>/ws/esp32
 *  - Sends hello on connect, state heartbeat every 1 s.
 *  - Receives: hello_ack, hb, gate commands, calibrate command.
 *  - Reconnects automatically on disconnect.
 *  - Link is "lost" if no server message for 3 s.
 * =====================================================================*/

#include "net.h"
#include "config.h"
#include "storage.h"
#include "slots.h"
#include "gates.h"
#include "sensors.h"
#include "display.h"

#if __has_include("secrets.h")
#include "secrets.h"
#elif __has_include("secrets.example.h")
#include "secrets.example.h"
#else
#define WIFI_SSID      "YourSSID"
#define WIFI_PASS      "YourPassword"
#define SERVER_IP      "192.168.137.1"
#define SERVER_PORT    8000
#endif

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

// Forward declaration for incoming message handler
static void handleMessage(const char* payload);

namespace Net {

    static WebSocketsClient _ws;
    static String _ssid;
    static String _pass;
    static String _serverIP;
    static uint16_t _serverPort;

    static bool _wsConnected = false;
    static bool _wsStarted = false;
    static bool _helloAcked = false;
    static unsigned long _lastServerMsg = 0;
    static unsigned long _lastHeartbeat = 0;
    static unsigned long _lastWifiCheck = 0;
    static bool _linkUp = false;

    // Calibration state (non-blocking would be better but calibrate() is inherently blocking)
    static bool _calRequested = false;

    // ---- WebSocket event handler ----
    static void wsEvent(WStype_t type, uint8_t* payload, size_t length) {
        switch (type) {
            case WStype_CONNECTED:
                _wsConnected = true;
                _helloAcked = false;
                Serial.printf("[Net] WebSocket connected to %s:%d\n",
                              _serverIP.c_str(), _serverPort);
                {
                    // Send hello
                    JsonDocument doc;
                    doc["t"] = "hello";
                    doc["fw"] = FW_VERSION;
                    doc["ip"] = WiFi.localIP().toString();
                    doc["calibrated"] = Slots::isCalibrated();

                    // Reset reason
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
                    _ws.sendTXT(buf);
                    Serial.printf("[Net] Sent: %s\n", buf);
                }
                break;

            case WStype_DISCONNECTED:
                _wsConnected = false;
                _helloAcked = false;
                _linkUp = false;
                Gates::setLinkUp(false);
                Serial.println(F("[Net] WebSocket disconnected"));
                break;

            case WStype_TEXT:
                _lastServerMsg = millis();
                handleMessage((const char*)payload);
                break;

            case WStype_PING:
            case WStype_PONG:
                _lastServerMsg = millis();
                break;

            default:
                break;
        }
    }

    // ---- Public API ----

    void begin() {
        // Load network settings from NVS (fallback to secrets.h defaults)
        _ssid = Storage::loadSSID(WIFI_SSID);
        _pass = Storage::loadPass(WIFI_PASS);
        _serverIP = Storage::loadServerIP(SERVER_IP);
        _serverPort = Storage::loadServerPort(SERVER_PORT);

        Serial.printf("[Net] Wi-Fi: %s\n", _ssid.c_str());
        Serial.printf("[Net] Server: %s:%d\n", _serverIP.c_str(), _serverPort);

        _wsConnected = false;
        _wsStarted = false;
        _helloAcked = false;
        _linkUp = false;

        // Start Wi-Fi
        WiFi.mode(WIFI_STA);
        WiFi.setAutoReconnect(true);
        WiFi.begin(_ssid.c_str(), _pass.c_str());
        Serial.println(F("[Net] Wi-Fi connecting..."));

        // Configure WebSocket (will connect once Wi-Fi is up)
        _ws.onEvent(wsEvent);
        _ws.setReconnectInterval(WS_RECONNECT_MS);

        _lastWifiCheck = millis();
        _lastServerMsg = millis();
        _lastHeartbeat = 0;
    }

    void update() {
        unsigned long now = millis();

        // --- Wi-Fi management ---
        if (WiFi.status() == WL_CONNECTED) {
            if (!_wsStarted) {
                _wsStarted = true;
                _ws.begin(_serverIP.c_str(), _serverPort, "/ws/esp32");
                Serial.printf("[Net] WebSocket client started to %s:%d/ws/esp32\n",
                              _serverIP.c_str(), _serverPort);
            }
            _ws.loop();
        } else {
            // Wi-Fi not connected
            if (_wsStarted) {
                _wsStarted = false;
                _wsConnected = false;
                _linkUp = false;
                Gates::setLinkUp(false);
            }
            if (now - _lastWifiCheck > 5000) {
                _lastWifiCheck = now;
                Serial.printf("[Net] Wi-Fi status: %d (connecting...)\n", WiFi.status());
            }
        }

        // --- Handle pending calibration request ---
        if (_calRequested) {
            _calRequested = false;
            Display::showMessage("CALIBRATING...", "Keep slots empty");

            bool ok = Slots::calibrate([](uint8_t done, uint8_t total) {
                // Send progress to server
                JsonDocument doc;
                doc["t"] = "cal_progress";
                doc["done"] = done;
                doc["total"] = total;
                char buf[64];
                serializeJson(doc, buf, sizeof(buf));
                Net::send(buf);
            });

            // Send cal_result
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

        // --- Link timeout detection ---
        if (_wsConnected) {
            if (now - _lastServerMsg > LINK_TIMEOUT_MS) {
                if (_linkUp) {
                    _linkUp = false;
                    Gates::setLinkUp(false);
                    Serial.println(F("[Net] Link LOST (no server messages)"));
                }
            } else if (_helloAcked && !_linkUp) {
                _linkUp = true;
                Gates::setLinkUp(true);
                Serial.println(F("[Net] Link UP"));
            }
        }

        // --- Send state heartbeat every 1 s ---
        if (_wsConnected && (now - _lastHeartbeat >= HEARTBEAT_MS)) {
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
                if (d >= 0) dist.add(serialized(String(d, 1)));
                else        dist.add(nullptr);

                fault.add(s == SLOT_FAULT ? 1 : 0);
            }

            doc["entry"]      = Gates::getStateStr(GATE_ENTRY);
            doc["exit"]       = Gates::getStateStr(GATE_EXIT);
            doc["calibrated"] = Slots::isCalibrated();
            doc["free"]       = Slots::freeCount();
            doc["uptime"]     = (uint32_t)(millis() / 1000);

            char buf[512];
            serializeJson(doc, buf, sizeof(buf));
            _ws.sendTXT(buf);
        }
    }

    bool isLinkUp() { return _linkUp; }

    bool send(const char* json) {
        if (!_wsConnected) return false;
        return _ws.sendTXT(json);
    }

    void setWifi(const char* ssid, const char* pass) {
        _ssid = ssid;
        _pass = pass;
        Storage::saveSSID(ssid);
        Storage::savePass(pass);
        Serial.printf("[Net] Wi-Fi credentials saved. Reconnecting to '%s'...\n", ssid);
        _ws.disconnect();
        _wsConnected = false;
        _wsStarted = false;
        WiFi.disconnect();
        WiFi.begin(_ssid.c_str(), _pass.c_str());
    }

    void setServer(const char* ip, uint16_t port) {
        _serverIP = ip;
        _serverPort = port;
        Storage::saveServerIP(ip);
        Storage::saveServerPort(port);
        Serial.printf("[Net] Server set to %s:%d. Reconnecting...\n", ip, port);
        _ws.disconnect();
        _wsConnected = false;
        _wsStarted = false;
    }

    String getIP() {
        return WiFi.localIP().toString();
    }

    bool isWifiConnected() {
        return WiFi.status() == WL_CONNECTED;
    }
}

// ---- Incoming message handler ----
static void handleMessage(const char* payload) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload);
    if (err) {
        Serial.printf("[Net] JSON parse error: %s\n", err.c_str());
        return;
    }

    const char* t = doc["t"];
    if (!t) return;

    if (strcmp(t, "hello_ack") == 0) {
        Net::_helloAcked = true;
        Serial.println(F("[Net] Received hello_ack"));

    } else if (strcmp(t, "hb") == 0) {
        // Server heartbeat — just updates _lastServerMsg (done in wsEvent)

    } else if (strcmp(t, "gate") == 0) {
        const char* gate   = doc["gate"];
        const char* action = doc["action"];
        uint16_t hold_ms   = doc["hold_ms"] | Gates::getHoldMs();
        const char* req_id = doc["req_id"] | "";

        if (!gate || !action) return;

        GateId gateId = (strcmp(gate, "entry") == 0) ? GATE_ENTRY : GATE_EXIT;

        if (strcmp(action, "open") == 0) {
            char reason[32] = "";
            bool ok = Gates::open(gateId, hold_ms, req_id, reason, sizeof(reason));

            // Send gate_result
            JsonDocument resp;
            resp["t"] = "gate_result";
            resp["gate"] = gate;
            resp["ok"] = ok;
            if (!ok) resp["reason"] = reason;
            if (strlen(req_id) > 0) resp["req_id"] = req_id;

            char buf[128];
            serializeJson(resp, buf, sizeof(buf));
            Net::send(buf);

        } else if (strcmp(action, "close") == 0) {
            Gates::close(gateId);
        }

    } else if (strcmp(t, "cmd") == 0) {
        const char* cmd = doc["cmd"];
        if (!cmd) return;

        if (strcmp(cmd, "calibrate") == 0) {
            Net::_calRequested = true;
        }
    }
}
