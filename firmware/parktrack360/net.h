#pragma once
/* =====================================================================
 *  ParkTrack 360 — net.h
 *  Wi-Fi connection + WebSocket client to the laptop server.
 * =====================================================================*/

#include <Arduino.h>

namespace Net {

    // Call once in setup()
    void begin();

    // Non-blocking update — handles Wi-Fi reconnect, WebSocket
    // reconnect, heartbeat sending, link timeout detection.
    // Call every loop iteration.
    void update();

    // Is the server link considered up?
    bool isLinkUp();

    // Send a JSON message to the server (if connected).
    // Returns true if sent successfully.
    bool send(const char* json);

    // Reconnect Wi-Fi with new credentials (saves to NVS).
    void setWifi(const char* ssid, const char* pass);

    // Set server address (saves to NVS and reconnects).
    void setServer(const char* ip, uint16_t port);

    // Get current network info
    String getIP();
    bool   isWifiConnected();
}
