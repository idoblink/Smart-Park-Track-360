"""
Interactive CLI Servo Test Tool for ParkTrack 360
Tests Entry (GPIO 23) and Exit (GPIO 15) servo motors independently.
Usage:
    python tools/test_servos.py
"""
import sys
import time
import json
import serial
import serial.tools.list_ports

def find_esp32_port():
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        if "cp210" in desc or "ch340" in desc or "usb" in desc or "com3" in p.device.lower():
            return p.device
    return "COM3"

def main():
    port = find_esp32_port()
    print(f"Connecting to ESP32 on {port} at 115200 baud...")
    try:
        ser = serial.Serial(port, 115200, timeout=1.0)
    except Exception as e:
        print(f"Error opening port {port}: {e}")
        print("Make sure Python server (python -m server.app) and Arduino Serial Monitor are closed!")
        return

    time.sleep(2.0)
    # Drain initial lines
    while ser.in_waiting:
        ser.readline()

    print("\n================ SERVO DIAGNOSTIC MENU ================")
    print("1 -> Open ENTRY gate  (GPIO 23 to 90° for 5s)")
    print("2 -> Open EXIT gate   (GPIO 15 to 90° for 5s)")
    print("3 -> Set angles 0 90  (Enforce 0° closed, 90° open)")
    print("4 -> Set angles 10 90 (Relax closed angle to 10° to stop buzzing)")
    print("q -> Quit")
    print("=======================================================")

    while True:
        choice = input("\nEnter choice (1/2/3/4/q): ").strip().lower()
        if choice == "q":
            break
        elif choice == "1":
            cmd = {"t": "gate", "gate": "entry", "action": "open", "hold_ms": 5000, "req_id": "test_cli"}
            msg = json.dumps(cmd) + "\n"
            ser.write(msg.encode())
            print(f"Sent: {msg.strip()}")
        elif choice == "2":
            cmd = {"t": "gate", "gate": "exit", "action": "open", "hold_ms": 5000, "req_id": "test_cli"}
            msg = json.dumps(cmd) + "\n"
            ser.write(msg.encode())
            print(f"Sent: {msg.strip()}")
        elif choice == "3":
            ser.write(b"angles 0 90\n")
            print("Sent: angles 0 90")
        elif choice == "4":
            ser.write(b"angles 10 90\n")
            print("Sent: angles 10 90 (relaxes bottom endstop to cure vibration)")
        else:
            print("Invalid choice")

        # Read responses for 1 second
        t_end = time.time() + 1.2
        while time.time() < t_end:
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    print(f"  [ESP32] {line}")
            time.sleep(0.05)

    ser.close()
    print("Serial port closed.")

if __name__ == "__main__":
    main()
