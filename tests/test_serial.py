import pytest
from server.serial_comm import ESP32SerialManager

def test_serial_manager_init():
    mgr = ESP32SerialManager(port="COM3", baudrate=115200)
    assert mgr.preferred_port == "COM3"
    assert mgr.baudrate == 115200
    assert not mgr.connected
    assert not mgr.running

def test_serial_manager_send_when_disconnected():
    mgr = ESP32SerialManager(port="COM3", baudrate=115200)
    # When not connected, send should return False without raising an exception
    result = mgr.send({"t": "gate", "action": "open"})
    assert result is False
