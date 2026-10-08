# ParkTrack 360 — v1.1 Build Specification

Self-contained spec for building the prototype. Give this file to the coding agent (Google Antigravity) as the **single source of truth**.

**Document status:** v1.1 supersedes v1.0. v1.1 keeps the v1.0 pin map, wiring and behaviour rules and adds implementation detail, camera options for a low budget, protocol schemas, database design, test procedures and an agent work plan. Anything that *clarifies or corrects* v1.0 is listed in section 14 so the owner can approve it.

**Priority tags** used in this file: **[MUST]** needed for acceptance tests, **[SHOULD]** build it unless it costs more than a few hours, **[COULD]** only if time remains. Items marked **[CONFIRM]** are open questions (section 13).

---

## 0. Rules for the coding agent

1. **Do not change the pin map (3.4), wiring, or behaviour rules (4, 5) without asking the owner.** If something looks wrong, write the concern in `docs/questions.md` and continue with the spec as written.
2. Work in the order of section 9. Finish and self-test one step before starting the next. At the end of each step write `docs/step-N-report.md`: what was built, how to run it, what the owner must verify on hardware, expected serial or console output.
3. The agent **cannot flash or wire hardware**. Firmware is compiled and uploaded by the owner in Arduino IDE 2.x. Every firmware step therefore ships with a test sketch and the exact output the owner should see.
4. Do not add features outside this spec. Do not add cloud services, login, RFID, payments, buzzer.
5. Never hard-code Wi-Fi passwords in committed files. Use `secrets.h` (firmware, git-ignored) and the NVS override commands in 5.7.
6. Everything tunable lives in `firmware/parktrack360/config.h` or `server/config.yaml`. No magic numbers in code.
7. The owner does not code. Provide `run_server.bat` (Windows) and `run_server.sh`, a `requirements.txt`, and a `README.md` with copy-paste setup steps.
8. Ask the owner (do not guess) for: Wi-Fi mode, camera hardware actually purchased, OLED size, PCF8574 vs PCF8574A.

---

## 1. Scope (v1.0 feature set, unchanged)

A 2-floor toy parking model (8 slots: G1–G4 ground, F1–F4 first floor) using Hot Wheels cars numbered 1–8.

| Feature | In v1.x |
|---|---|
| 8 slot sensors (HC-SR04) → occupied/vacant | Yes |
| Red/green LED per slot (via 2× PCF8574) | Yes |
| OLED status display (SSD1306, I²C) | Yes |
| 2 servo barrier gates (entry, exit) | Yes |
| 2 gate indicator LED pairs | Yes |
| **Single USB webcam** covering both entry and exit lanes, reading the car number (1–8) | Yes (one physical camera, two ROIs) |
| Browser dashboard, near-real-time, shows car-in-slot | Yes |
| Statistics (entries, exits, peak, dwell time) | Yes |
| Buzzer | **Removed completely** |
| RFID, payments, booking, cloud (Blynk/Firebase/ThingsBoard), login | No (future scope) |

---

## 2. Architecture

```
 Single USB webcam ──> LAPTOP (Python) ───┤
                     • YOLO26n digit    │
                       detector (CPU)   │ WebSocket (JSON)
                     • FastAPI server   │
                     • SQLite           ▼
                                    ESP32 DevKit V1
                     8× HC-SR04, 2× PCF8574 (16 slot LEDs), OLED,
                     2× servo, 2× gate LED pair
```

- **The ESP32 cannot run YOLO.** It only does sensing, LEDs, OLED, servos, and obeys commands. All "calculation" about car numbers happens on the **laptop**.
- **Fail-safe:** if the laptop link drops, the ESP32 keeps sensing, updating LEDs and OLED; both gates stay **closed** (4.4).
- Laptop is the single place that decides *whether a car may enter or exit*. The ESP32 can only **refuse** (full, uncalibrated, busy), never approve on its own.

### 2.1 Network options (pick one; ask the owner)

ESP32 supports **2.4 GHz Wi-Fi only**. Phones and laptop must be on the same subnet and client isolation must be off.

| Option | How | Pros | Cons |
|---|---|---|---|
| **A. Windows Mobile Hotspot (recommended if phones are used as cameras)** | Laptop shares its connection as a hotspot, band = 2.4 GHz. Laptop address is normally `192.168.137.1`. | Fixed laptop IP for free, no phone needed as router, works with no internet | Laptop may lose its own Wi-Fi unless it has Ethernet/USB tethering; some Wi-Fi adapters don't support it |
| **B. Phone hotspot** (v1.0 default) | ESP32 + laptop join the phone hotspot (2.4 GHz / "maximize compatibility") | Easy | Phone cannot also serve as a camera; laptop IP can change (reserve it or read it from `ipconfig`) |
| **C. Home/lab router** | Same router for both, DHCP reservation for the laptop | Most stable | College Wi-Fi often blocks device-to-device traffic, so only use a router you control |

The ESP32 learns the server address from NVS (5.7), so changing network never needs a re-flash.

### 2.2 Ports

| Port | Use |
|---|---|
| 8000/TCP | FastAPI: dashboard, `/ws/ui`, `/ws/esp32`, MJPEG streams, API |

On first run Windows Firewall asks to allow Python: tick **Private networks**. Without this the ESP32 and other devices cannot connect.

---

## 3. Hardware

### 3.1 Board
ESP32 DevKit V1, **30-pin** version (15 pins per side), micro-USB. Arduino board setting: **ESP32 Dev Module**. GPIO0 is **not** exposed on this board. Silkscreen aliases: VP = GPIO36, VN = GPIO39, RX2 = GPIO16, TX2 = GPIO17, TX0 = GPIO1, RX0 = GPIO3.

GPIO16/17 are used for sensing, so the module must be **ESP32-WROOM** (no PSRAM). Check with a one-line sketch printing `ESP.getPsramSize()`; `0` = WROOM = OK. If it is WROVER, GPIO16/17 are unusable and the owner must be asked before any change.

### 3.2 Parts (bill of materials)

| Qty | Part | Note |
|---|---|---|
| 1 | ESP32 DevKit V1 (30-pin) | |
| 8 | HC-SR04 | 5 V |
| 2 | PCF8574 modules | check whether PCF8574 or PCF8574**A** |
| 1 | SSD1306 I²C OLED | 128×64 assumed [CONFIRM] |
| 2 | Servo, 5 V (SG90 / MG90S class) | barrier gates |
| 8 + 8 | Red + green LED | slot LEDs |
| 2 + 2 | Red + green LED | gate LEDs |
| 20 | 220 Ω resistor | one per LED |
| 8 + 8 | 1 kΩ + 2 kΩ resistors | ECHO dividers |
| 1 | 5 V 2 A external supply | sensors + servos |
| 1 | 470–1000 µF capacitor | across servo 5 V rail (recommended) |
| — | Breadboards, jumpers, standoffs, card/foam board | |
| 1 | **USB webcam** (single camera shared by entry and exit) | |
| ~20 | Printed matte tag labels | see 6.2.3 |

### 3.3 Power
- ESP32: USB from laptop.
- Sensors, servos: external 5 V 2 A supply only. **Never** from ESP32 pins. Budget: 8 × HC-SR04 ≈ 120 mA, 2 × SG90 stall ≈ 1.3 A worst case, so the 2 A supply is enough if gates move one at a time.
- **All grounds common** (external supply GND, ESP32 GND, sensors, PCF8574s, servos, LED returns).
- PCF8574 modules and OLED powered from ESP32 **3.3 V** (keeps I²C at 3.3 V). Most breakout modules already have 4.7–10 kΩ pull-ups on SDA/SCL; three modules in parallel is fine.
- HC-SR04 TRIG is driven at 3.3 V, which works for HC-SR04 (high threshold ≈ 2 V). ECHO is 5 V and **must** go through the divider.

### 3.4 Final pin map (unchanged from v1.0)

**HC-SR04** (VCC 5 V, GND common). Every ECHO line goes through 1 kΩ (from ECHO) → junction → 2 kΩ (to GND); the ESP32 pin connects to the junction.

| Slot (index) | TRIG GPIO | ECHO GPIO | Note |
|---|---|---|---|
| G1 (0) | 13 | 34 | |
| G2 (1) | 14 | 35 | |
| G3 (2) | 27 | 36 | ECHO on board pin **VP** |
| G4 (3) | 26 | 39 | ECHO on board pin **VN** |
| F1 (4) | 25 | 18 | |
| F2 (5) | 33 | 5 | GPIO5 is a boot-strap pin; it is only an input after boot, fine |
| F3 (6) | 32 | 17 | ECHO on board pin **TX2** |
| F4 (7) | 19 | 16 | ECHO on board pin **RX2** |

**I²C bus** (shared): SDA = GPIO21, SCL = GPIO22. OLED at 0x3C (SSD1306; some modules are 0x3D). PCF8574 #1 = 0x20 (ground floor), #2 = 0x21 (first floor). **Verify with an I²C scan**; if the modules are PCF8574**A**, addresses are 0x38–0x3F. Addresses are constants in `config.h`. Default bus clock **100 kHz** (PCF8574 safe); 400 kHz is allowed only after it is tested.

**Slot LEDs — active-LOW wiring:** each LED: 3.3 V → 220 Ω → LED anode; LED cathode → PCF8574 pin. Writing **LOW lights the LED**, HIGH turns it off (PCF8574 can sink ~25 mA but source only ~100–300 µA). About 6 mA per LED.

| Slot | Green pin | Red pin | | Slot | Green pin | Red pin |
|---|---|---|---|---|---|---|
| G1 | P0 | P1 | | F1 | P0 | P1 |
| G2 | P2 | P3 | | F2 | P2 | P3 |
| G3 | P4 | P5 | | F3 | P4 | P5 |
| G4 | P6 | P7 | | F4 | P6 | P7 |

G* on expander 0x20, F* on expander 0x21. Firmware writes **one byte per expander** over raw `Wire`.

Byte rule for slot `i` on its floor (`i` = 0..3): green bit = `2i`, red bit = `2i+1`. Start from `0xFF`; clear (set to 0) the bit that must light.

| State per slot | Bits |
|---|---|
| Vacant | green bit 0, red bit 1 |
| Occupied | red bit 0, green bit 1 |
| Unknown / uncalibrated | both bits 1 (both LEDs off) |
| Sensor fault | green bit 1, red bit toggles at 1 Hz |

Self-test values: all four slots vacant on a floor = `0xAA`; all four occupied = `0x55`; all off = `0xFF`; all on = `0x00`.

**Servos:** Entry signal = GPIO23, Exit signal = GPIO15 (external 5 V + common GND). GPIO15 may twitch the servo at power-up; accepted. Servo signal wire runs at 3.3 V logic, which SG90/MG90S accept.

**Gate LED pairs (complementary, one GPIO each):**
- Green: GPIO → 220 Ω → green LED → GND
- Red: 3.3 V → 220 Ω → red LED → same GPIO
- GPIO HIGH = green on / red off. GPIO LOW = red on / green off.

| Pair | GPIO |
|---|---|
| Entry | 4 |
| Exit | 2 |

During reset/boot (pin floating) a pair may glow dimly; that is expected. GPIO2 is a boot-strapping pin. If an upload ever fails with a boot-mode error, disconnect the exit-pair lead and retry.

**Unused:** GPIO0 (not exposed), GPIO12 (avoid; boot strap), GPIO1/GPIO3 (USB serial, keep for debugging). Buzzer removed; GPIO1 unconnected.

### 3.5 Mounting guidance (sensors)

- **Default (overhead):** sensor faces down at each slot from the deck above (ground floor: underside of the first-floor deck; first floor: a roof beam). Baseline distance 8–12 cm.
- Hot Wheels cars are only about 1.5–2 cm tall, so the occupied signal is the baseline dropping by roughly the car height. HC-SR04 resolution is ~0.3 cm, so the 1.5 cm margin is tight. **Measure the owner's tallest and lowest car [CONFIRM #4]** and set `OCCUPIED_MARGIN_CM` ≈ 60–70 % of the *lowest* car height.
- Keep ≥ 5 cm between the sensor face and the car roof so the echo is not inside the HC-SR04 dead zone.
- **Fallback if overhead is unreliable (curved roofs scatter the echo):** mount each sensor on the back wall of the slot facing along the slot. Distance changes from ~15 cm (empty) to ~4 cm (car at the stopper) which is a much larger signal. No firmware change; only re-calibrate. Add a stopper so the car never sits closer than 3 cm.
- Cover or space sensors so that neighbouring sensors do not see each other's echoes (cardboard side walls between slots).

---

## 4. Behaviour rules

### 4.1 Slot sensing

Terminology: **round** = one pass over all 8 sensors.

- Read sensors **sequentially**, never together. Trigger pulse 10 µs, echo timeout ≈ 8000 µs (≈ 137 cm), ≥ **15 ms** gap between one sensor finishing and the next triggering. Distance in cm = echo µs / 58.3.
- A round therefore takes ≈ 130–190 ms. The same sensor is read once per round, so the ≥ 60 ms per-sensor gap is automatically met.
- **Median of 3:** after every round, each slot's value is the **median of its latest 3 round readings** (sliding window). Readings < 2 cm or timeouts are *invalid* and excluded from the median.
- **Occupied** if `distance ≥ 2 cm` and `distance < baseline − margin`. Default margin **1.5 cm** (`OCCUPIED_MARGIN_CM`).
- **Debounce:** a slot changes state only after **3 consecutive rounds** agree on the new state.
- Resulting latency from physical change to dashboard ≈ 0.45–0.6 s on a healthy network, which meets the **< 1 s** target. (Taking 3 *separate* readings per sensor and then 3 debounced cycles would cost ≈ 1.4 s and fail the target; that is why the sliding window is used. See section 14, item 1.)
- **Sensor fault:** if a slot returns invalid readings for 10 consecutive rounds it enters `fault`: dashboard shows a warning, red LED blinks, the slot is counted as **not available** for entry decisions. It recovers automatically after 3 consecutive valid rounds.

### 4.2 Calibration

- Command `calibrate` (dashboard button, or serial) with **all slots empty**: take **15 rounds**, store each sensor's median as `baseline_cm`, save in ESP32 NVS (`Preferences`). Progress and results go to the dashboard.
- A slot's calibration is **rejected** if its 15 readings spread (max − min) > 1.0 cm, more than 3 readings are invalid, or baseline is < 4 cm or > 100 cm. The report lists failing slots by name. `calibrated` becomes true only when all 8 slots have a valid baseline. Accepted slots keep their new values.
- If no baseline is stored, the firmware reports `uncalibrated` and treats all slots as unknown (LEDs off, entry gate refuses to open, OLED shows "CALIBRATE").
- Dashboard shows a confirmation dialog: "Make sure ALL slots are empty."

### 4.3 LEDs and OLED

- Slot LED: vacant = green, occupied = red.
- Entry gate pair: green when free slots > 0, red when full (and red while uncalibrated).
- Exit gate pair: green while the exit gate is open, red otherwise.
- OLED (128×64, text size 1, rows at y = 0, 16, 32, 48; a 128×32 panel also fits at y = 0, 8, 16, 24):
```
SMART PARKING
Total Slots : 8
Occupied    : N
Available   : M
```
When M = 0, replace the last line with `PARKING FULL`. When uncalibrated show `CALIBRATE` centred. Redraw only on change (not every loop). **[COULD]** `OLED_SHOW_LINK` flag (default off) draws a small link-up indicator in the top-right corner.
- `free` = number of slots that are calibrated, valid, not occupied and not faulty.

### 4.4 Gates (servo)

- Defaults (tune on hardware, all in `config.h`): closed = 0°, open = 90°, hold open **5000 ms**, then close. Pulse range 500–2400 µs, 50 Hz.
- Movement is **non-blocking and gradual**: step 2° every 15 ms (≈ 0.7 s for 90°). This limits inrush current and keeps Wi-Fi alive.
- Gate state machine (per gate): `CLOSED → OPENING → OPEN (hold timer) → CLOSING → CLOSED`. A second open command while `OPEN` restarts the hold timer. An open command while `CLOSING` reverses to opening. `close` closes immediately (via `CLOSING`).
- **Entry:** the server may request open only when a car has been read and approved. The ESP32 **independently refuses** an entry-open when `free = 0`, when `uncalibrated`, or when the link is down. Refusals return a `gate_result` message with the reason (6.1).
- **Exit:** opens when the server approves an exit read. No slot check.
- `hold_ms` from the server is clamped to 1000–15000 ms.
- Gates start closed at boot (attach servos and write the closed angle in `setup()`).
- **Link lost:** close any open gate after its hold time (do not extend), refuse all open commands until the link is back **and** a fresh `hello_ack` arrived.
- v1.x has **no sensor for "car has passed the gate"**; the gate closes on the timer only. Known limitation, see section 11.

### 4.5 Link monitoring (ESP32 side)

- The ESP32 sends a `state` heartbeat every 1 s. The server sends `{"t":"hb"}` every 1 s.
- The ESP32 considers the link **lost** if it receives nothing for **3 s** (`LINK_TIMEOUT_MS`) or the WebSocket reports DISCONNECTED.
- Wi-Fi and WebSocket reconnect run in the background with a 2 s retry; `loop()` must never block waiting for Wi-Fi. Sensing, LEDs and OLED continue regardless.

---

## 5. Car logic (server-side) and firmware modules

### 5.1 Car states

Cars are numbered 1–8 (single digit). Each car is in one state:

`OUTSIDE → ENTERED (gate passed, no slot yet) → PARKED(slot) → ENTERED (slot vacated) → OUTSIDE (exit read)`

**Entry approval** (entry camera produces a stable read of car N, section 6.3):
1. Car N must be `OUTSIDE`; otherwise deny ("already inside").
2. `free_for_entry = free_slots − (cars currently in ENTERED state)` must be > 0; otherwise deny ("full").
3. ESP32 must be online and calibrated; otherwise deny ("controller offline" / "uncalibrated").
4. Approve → send `gate entry open`, set N = `ENTERED`, count an entry, open a `visit` record.
5. If the ESP32 answers `gate_result` with `ok:false`, **roll back**: N returns to `OUTSIDE`, the entry is not counted, event `deny` logged with the ESP32's reason.

**Exit approval** (exit camera produces a stable read of car N):
1. N must not be `OUTSIDE`; otherwise deny ("not inside").
2. Approve → send `gate exit open`, set N = `OUTSIDE`, free its slot association, count an exit, close the visit (record `inside_s` and `parked_s`).

**Car-in-slot association (heuristic, as agreed):** when a slot becomes occupied, assign the **oldest `ENTERED` car** to it. If no car is `ENTERED`, mark the slot occupant as `Unknown`. When a slot becomes vacant, its car returns to `ENTERED` (if it had a known car). Log a warning if a car stays `ENTERED` > 120 s.

**Edge cases (explicit):**
| Situation | Rule |
|---|---|
| Exit read for a car that is `PARKED(slot)` while the slot still shows occupied | Approve the exit, clear the association; when the slot later turns vacant there is no car to return, log `slot_vacated_no_car` |
| Slot vacant event while occupant is `Unknown` | Just clear the slot |
| Slot occupied with no `ENTERED` car (e.g. car placed by hand) | Occupant `Unknown`; operator may correct it on the dashboard (9, controls) |
| Server restarts | Car states reloaded from the `car_state` table; slot occupancy re-read from the next ESP32 `state` message; any mismatch is logged and resolved as `Unknown` |
| ESP32 offline | Entry and exit reads are shown but **denied** ("controller offline"); stats are untouched |
| Manual gate open from dashboard | Gate opens (subject to ESP32 refusals), car states are **not** changed, event `manual_gate` logged |

**Cooldown and re-arm (per lane ROI):** after a gate cycle, ignore new reads for **8 s** (`cooldown_s`). In addition, the camera is **re-armed only after the ROI has been empty (no detections) for ≥ 1 s** (`rearm_empty_s`). This stops a car sitting under the camera from being counted twice.

### 5.2 Physical demo flow (for the viva)
1. Operator puts car N on the entry lane under the camera. Dashboard shows the read and "Entry approved". Entry gate opens for 5 s.
2. Operator pushes the car through and parks it in a slot. The slot LED turns red; the dashboard tile shows "Car N".
3. To leave: operator lifts the car out of the slot (tile turns green, car N returns to `ENTERED`), places it under the exit camera, exit gate opens, stats update.

### 5.3 Firmware modules (Arduino IDE, one sketch, multiple tabs)

`firmware/parktrack360/` contains `parktrack360.ino` plus: `config.h`, `secrets.h` (git-ignored, `secrets.example.h` committed), `sensors.h/.cpp`, `slots.h/.cpp` (baseline, median, debounce, fault), `leds.h/.cpp` (PCF8574 bytes, gate pairs), `display.h/.cpp`, `gates.h/.cpp` (state machine), `net.h/.cpp` (Wi-Fi, WebSocket, JSON), `storage.h/.cpp` (NVS), `serial_cmd.h/.cpp`.

The **folder name must equal the main `.ino` name** or Arduino IDE refuses to open it (this fixes a v1.0 layout mistake).

Main loop is cooperative: each module exposes `update()` that returns quickly; only `sensors` may block, for ≤ 8 ms per read.

### 5.4 `config.h` template (agent must create; values are defaults)

```cpp
#pragma once
#include <Arduino.h>

// ---- Pins (DO NOT CHANGE without owner approval) ----
static const uint8_t TRIG_PINS[8] = {13, 14, 27, 26, 25, 33, 32, 19};
static const uint8_t ECHO_PINS[8] = {34, 35, 36, 39, 18, 5, 17, 16};
#define PIN_SDA          21
#define PIN_SCL          22
#define PIN_SERVO_ENTRY  23
#define PIN_SERVO_EXIT   15
#define PIN_GATELED_ENTRY 4
#define PIN_GATELED_EXIT  2

// ---- I2C ----
#define ADDR_OLED        0x3C
#define ADDR_PCF_GROUND  0x20   // 0x38 if PCF8574A
#define ADDR_PCF_FIRST   0x21   // 0x39 if PCF8574A
#define OLED_W           128
#define OLED_H           64
#define I2C_CLOCK_HZ     100000

// ---- Sensing ----
#define ECHO_TIMEOUT_US      8000
#define SENSOR_GAP_MS        15
#define MEDIAN_WINDOW        3
#define DEBOUNCE_ROUNDS      3
#define MIN_VALID_CM         2.0f
#define OCCUPIED_MARGIN_CM   1.5f
#define CAL_ROUNDS           15
#define CAL_MAX_SPREAD_CM    1.0f
#define FAULT_ROUNDS         10

// ---- Gates ----
#define SERVO_CLOSED_DEG   0
#define SERVO_OPEN_DEG     90
#define SERVO_STEP_DEG     2
#define SERVO_STEP_MS      15
#define SERVO_MIN_US       500
#define SERVO_MAX_US       2400
#define GATE_HOLD_MS       5000
#define GATE_HOLD_MIN_MS   1000
#define GATE_HOLD_MAX_MS   15000

// ---- Network ----
#define HEARTBEAT_MS       1000
#define LINK_TIMEOUT_MS    3000
#define WS_RECONNECT_MS    2000
#define DEFAULT_SERVER_PORT 8000
// SSID/password/server IP come from secrets.h and can be overridden in NVS.
```

### 5.5 NVS (`Preferences`, namespace `pt360`)

Keys: `base0`…`base7` (float cm), `cal` (bool), `margin` (float), `closed`, `open`, `hold` (ints), `ssid`, `pass`, `srv_ip`, `srv_port`. A value in NVS overrides `config.h`/`secrets.h`.

### 5.6 JSON library notes
Use **ArduinoJson 7** (`JsonDocument`); use the **WebSockets** library by Markus Sattler (`WebSocketsClient`). Compile with the latest stable Espressif core; if `ESP32Servo` fails to compile with a new core, the agent must report the exact error in `docs/questions.md` rather than switching libraries silently.

### 5.7 Serial commands (115200 baud, newline terminated)

| Command | Effect |
|---|---|
| `help` | list commands |
| `status` | print slots, distances, baselines, gates, link, free count |
| `calibrate` | run calibration (4.2) |
| `gate entry open` / `gate entry close` / `gate exit open` / `gate exit close` | manual gate control (entry still refuses when full/uncalibrated) |
| `wifi <ssid> <password>` | store credentials in NVS and reconnect |
| `server <ip> <port>` | store server address in NVS and reconnect |
| `margin <cm>` | set occupied margin |
| `angles <closed> <open>` | set servo angles |
| `hold <ms>` | set hold time |
| `scan` | I²C scan |
| `ledtest` | walk through all LEDs |
| `reboot` | restart |

This lets the owner fix network or tuning issues from the Arduino Serial Monitor without touching code.

---

## 6. Vision pipeline (laptop, Python)

### 6.1 Model
- **Ultralytics YOLO26n** (`yolo26n.pt`). It is the current Ultralytics model line and is designed for CPU/edge use: end-to-end (no NMS step) and exportable to ONNX/OpenVINO for faster CPU inference. If unavailable, `yolo11n.pt` is a drop-in fallback (same API).
- Single detector with **8 classes named "1" … "8"** (the car number). One detection = one car ID. Include 10–15 % **negative images** (no tag, empty lane, hands, other objects) with empty label files to suppress false positives.
- Inference on **CPU** (owner request), `imgsz=640`, on a **cropped ROI** of the lane (per-lane ROI in config), ~10 FPS cap. Export the trained model to **ONNX** (`format="onnx"`), or **OpenVINO** (`format="openvino"`) on an Intel CPU, and run the exported file on the server. Target ≤ 80 ms per ROI on the owner's laptop (`tools/benchmark.py` reports this). Config switch `vision.device` allows `cpu` or `0` (NVIDIA GPU) without code changes.
- If the CPU is too slow: reduce ROI size first, then retrain at `imgsz=480`.

### 6.2 Cameras

#### 6.2.1 What the vision needs (camera-agnostic requirements)
- Overhead mount, looking straight down at the tag on the roof/hood.
- **Digit height in the frame ≥ 30 px** (40 px preferred), tag in **sharp focus**, no strong glare.
- Fixed exposure/focus after setup; same camera model for **training data and demo** (domain match matters more than megapixels).

Pixel rule: `px_per_mm = image_width_px / scene_width_mm`, `scene_width_mm ≈ 2 × distance_mm × tan(HFOV/2)`. For a typical cheap webcam with ~60° horizontal FOV at 1280 px width:

| Camera height | Scene width | px per mm | 12 mm digit height |
|---|---|---|---|
| 25 cm | ≈ 29 cm | ≈ 4.4 | ≈ 53 px |
| 30 cm | ≈ 35 cm | ≈ 3.7 | ≈ 44 px |
| 40 cm | ≈ 46 cm | ≈ 2.8 | ≈ 33 px |

At 640×480 the same distances give roughly half those pixel counts, so use ≤ 25 cm or bigger digits. The lane only needs a ROI of about 10 × 10 cm around the tag, so the crop passed to YOLO is ≈ 300–450 px and is **not downscaled** (good for small digits).

#### 6.2.2 Camera selection — single USB webcam

Use **one USB webcam** for both the entry and exit lanes. Mount it so both lanes are visible in the same frame, with a separate ROI for each lane. The two ROIs are independent in software but use the same physical camera and video stream.

Recommended starting point:
- USB webcam with native **1280×720** output and adjustable/fixed focus that is sharp at the planned mounting distance.
- Mount overhead and centered so both entry and exit tags are clearly visible.
- Keep the entry and exit lanes close enough that both fit comfortably inside the camera's field of view while preserving at least **30 px digit height** in each ROI.
- The camera is connected to the laptop by USB; no phone camera, IP camera, ESP32-CAM, or second webcam is required.

**Decision procedure:**
1. Mount the single USB webcam at the planned height.
2. Run `tools/camera_probe.py` to confirm the webcam exposes 1280×720.
3. Run `tools/focus_test.py` and verify that digits in **both** lanes are sharp and ≥ 30 px high.
4. Run `tools/roi_picker.py` twice to define the entry ROI and exit ROI from the same camera frame.
5. Collect the final training dataset using this same webcam and mounting position. Do not train on another camera and then switch cameras for the demo.
6. If the webcam is blurry at the required distance, adjust mounting height/focus or use a close-up lens; do not add a second camera.

Note on "1080p" at this price: many ₹600 webcams are 720p sensors that are interpolated. Use the native 1280×720 mode and judge by the focus/pixel test, not the box.

#### 6.2.3 Tag design (strongly recommended: printed, not hand-drawn)

- Print the digits 1–8 from a bold, plain font in which **1 has a foot** and 7 has no crossbar (e.g. *DejaVu Sans Mono Bold*), black on white, on **matte** sticker paper. Label ≈ 14 × 18 mm, digit height **≥ 12 mm**, ≥ 2 mm white margin.
- Every car carries its tag on the roof/hood, **same orientation on all cars** (top of digit toward the car's front) and the cars always enter the lane front-first.
- Matte tape only; glossy tape causes glare. Soft, diffuse light (white card reflector or a LED strip bounced off a wall), no spot lights.
- Hand-drawn digits (thick black marker) still work but raise 1/7 and 3/8 confusion risk; if used, collect those cases deliberately.
- Print 2 spare labels per car.

#### 6.2.4 Camera configuration and tools

- Resolution request: 1280×720, 30 FPS. On Windows use `cv2.VideoCapture(index, cv2.CAP_DSHOW)` and request **MJPG** (`CAP_PROP_FOURCC`). Only one USB webcam is used, so there is no multi-camera USB bandwidth requirement.
- Lock focus where supported: `CAP_PROP_AUTOFOCUS=0`, then `CAP_PROP_FOCUS`. Exposure: `CAP_PROP_AUTO_EXPOSURE` and `CAP_PROP_EXPOSURE` are driver-dependent (DirectShow often uses negative values such as −6); the config stores whatever works and the camera tool reports which properties the driver accepted. Fixed-focus webcams simply ignore the focus properties.
- `source` in `config.yaml` is the USB webcam device index (normally `0`). A video file path may also be used for offline replay/testing.
- Capture runs in its own thread that always keeps **only the newest frame**; inference reads the newest frame and drops older ones to avoid lag.

Tools the agent must supply:
- `tools/camera_probe.py`: lists camera indices, supported resolutions, which properties are settable.
- `tools/focus_test.py`: live preview with a **sharpness score** (variance of the Laplacian) over the ROI, plus an on-screen px-per-mm and digit-height readout (the user types the real digit height in mm). Pass criteria: stable score, digit ≥ 30 px, edges visibly crisp.
- `tools/roi_picker.py`: drag a rectangle on the live image; writes the ROI into `config.yaml`.

### 6.3 Stable read (prevents wrong gate opens)

A read is accepted only if **all** hold:
- The **same class** is detected in **≥ 5 consecutive frames** (`stable_frames`) with confidence **≥ 0.70** (`min_conf`), both configurable.
- Exactly **one distinct class** is present in the ROI (duplicate boxes of the same class are merged; two different classes = `conflict` = unreadable).
- Box area ≥ `min_box_px` (default 24 × 24 px) and box centre inside the central 80 % of the ROI.
- Lane ROI is armed (cooldown and re-arm rules, 5.1).

Anything else is "unreadable": gate stays closed, event `unreadable` logged (rate-limited to once per 3 s per lane), reason shown on the dashboard (`low_conf`, `conflict`, `too_small`, `no_tag`). A frame with no detection resets the streak.

### 6.4 Dataset and training

- `tools/collect.py`: preview a camera, press 1–8 to save the current ROI crop and full frame into `dataset/raw/<number>/`; press `n` to save a negative into `dataset/raw/negative/`; shows live counts per class. Saves at most 5 images per second.
- Collect **≥ 60 images per number (≥ 500 total, 100 per number preferred)** from the final mounting position(s), with tilt, small position shifts, lighting changes, glare, partial shadow, plus 10–15 % negatives. Collect **in several separate sessions** (different times/lighting). Deliberately collect confusing pairs (1 vs 7, 3 vs 8, 5 vs 6).
- Label bounding boxes (one tight box per tag) with Roboflow or Label Studio, export in YOLO format. **[SHOULD]** Speed-up: train a quick model on the first ~15 images per class, use it to pre-label the rest, then correct the boxes.
- Split **by session**: ≈ 70 % train / 15 % val / 15 % test, never mixing the same session across splits. (v1.0 said 80/20; a held-out test set is recommended.)
- `vision/data.yaml`: `names: {0: "1", 1: "2", ... 7: "8"}`. Class index = number − 1; the server converts it.
- `vision/train.py` (device from argument, default `0` if CUDA is available else asks the owner to use Colab):

```python
from ultralytics import YOLO
model = YOLO("yolo26n.pt")          # fallback: yolo11n.pt
model.train(
    data="vision/data.yaml", imgsz=640, epochs=100, patience=30, batch=16,
    device=0, seed=0, project="runs", name="parktrack_v1",
    fliplr=0.0, flipud=0.0,          # NEVER mirror digits
    degrees=10, translate=0.10, scale=0.30, perspective=0.0005,
    hsv_h=0.015, hsv_s=0.5, hsv_v=0.4, mosaic=1.0, close_mosaic=10,
)
model.export(format="onnx", imgsz=640)   # or "openvino" on an Intel CPU
```

- Training location [CONFIRM #5]: local NVIDIA GPU with CUDA PyTorch, otherwise a free Google Colab GPU (the agent supplies a `vision/train_colab.ipynb` or a copy-paste cell block).
- The model is accepted by the **acceptance tests (section 11)**, not mAP alone. Also review the **confusion matrix** and per-class recall; any class < 95 % recall needs more data of that digit.
- `tools/replay.py`: run the full stable-read logic over a recorded video or a folder of images and print what would have happened (no hardware). Used to tune `stable_frames`, `min_conf`.
- `tools/benchmark.py`: reports inference ms per ROI on the current device.

---

## 7. Server (laptop)

- Python 3.11+, **FastAPI + uvicorn**, `websockets`, OpenCV, Ultralytics (+ `onnxruntime`, or `openvino`), SQLite (`sqlite3` from stdlib). Static dashboard (plain HTML/JS/CSS, no build step) served by FastAPI. `requirements.txt` with pinned versions and a one-command start script.
- Endpoints: `GET /` dashboard · `WS /ws/ui` browser · `WS /ws/esp32` controller · `GET /stream/entry` and `/stream/exit` (MJPEG with detection boxes, ~8 FPS, JPEG quality 70) · `GET /api/stats` · `GET /api/events?limit=50` · `GET /api/state` (same snapshot as WS) · `POST /api/gate` · `POST /api/calibrate` · `POST /api/reset_counters` · `POST /api/assign_slot` · `GET /healthz`.
- Only **one** ESP32 connection is accepted at a time; a new connection replaces the old one.
- Server pushes `{"t":"hb"}` to the ESP32 every 1 s and marks it **offline** if no `state` arrived for 3 s.
- Rotating log file `logs/server.log` (5 × 1 MB).
- All state transitions live in `state.py` as **pure functions** so they can be unit-tested with `pytest` (cases for every row of the car-logic tables). The agent supplies these tests.

### 7.1 `config.yaml` (template)

```yaml
server: {host: 0.0.0.0, port: 8000}
timezone: Asia/Kolkata
esp32: {stale_after_s: 3, heartbeat_s: 1}
gate: {hold_ms: 5000, cooldown_s: 8, rearm_empty_s: 1.0}
entered_warn_s: 120
vision:
  model: vision/best.onnx
  device: cpu            # or 0 for NVIDIA GPU
  imgsz: 640
  max_fps: 10
  stable_frames: 5
  min_conf: 0.70
  min_box_px: 24
camera:
  source: 0                    # single USB webcam index
  backend: dshow
  width: 1280
  height: 720
  fps: 30
  fourcc: MJPG
  autofocus: false
  focus: null                  # set by focus_test
  exposure: null
  entry_roi: [440, 160, 400, 400] # x, y, w, h (set by roi_picker)
  exit_roi: [840, 160, 400, 400]  # x, y, w, h (set by roi_picker)
```

### 7.2 Database (SQLite, `parktrack.db`)

```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,                 -- ISO 8601, local time
  type TEXT NOT NULL,               -- entry, exit, deny, slot_change, calibrate,
                                    -- esp32_connect, esp32_disconnect, unreadable,
                                    -- manual_gate, warning
  car INTEGER, slot TEXT, detail TEXT
);
CREATE TABLE visits (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  car INTEGER NOT NULL, entry_ts TEXT NOT NULL, exit_ts TEXT,
  inside_s REAL, parked_s REAL      -- inside_s = exit-entry; parked_s = sum of parkings
);
CREATE TABLE parkings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  visit_id INTEGER, car INTEGER, slot TEXT NOT NULL,
  start_ts TEXT NOT NULL, end_ts TEXT
);
CREATE TABLE car_state (
  car INTEGER PRIMARY KEY, state TEXT NOT NULL,   -- OUTSIDE / ENTERED / PARKED
  slot TEXT, entered_ts TEXT, visit_id INTEGER
);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);  -- stats_epoch_ts, schema_version
CREATE INDEX idx_events_ts ON events(ts);
```

`car_state` is pre-filled with cars 1–8 = `OUTSIDE`. "Reset counters" stores a new `stats_epoch_ts`; it does **not** change car states. "Today" is measured in server local time (IST).

### 7.3 `/api/stats` response

```json
{"entries_today":5,"exits_today":3,"occupied_now":2,"peak_today":4,"peak_all_time":6,
 "per_car":[{"car":1,"visits_today":2,"avg_inside_s":184.2,"avg_parked_s":150.1,"last_inside_s":201.0}],
 "epoch_ts":"2026-10-08T09:00:00+05:30"}
```

---

## 6.5 / 7.4 WebSocket protocol (JSON)

All messages are one JSON object per frame with a `t` field. Unknown `t` values are ignored and logged. Slot order everywhere: **G1,G2,G3,G4,F1,F2,F3,F4** (index 0–7).

### ESP32 → server

```json
{"t":"hello","fw":"1.1.0","ip":"192.168.137.23","calibrated":true,"reset_reason":"power_on"}
```
Sent once after each (re)connect.

```json
{"t":"state","slots":[0,1,0,0,0,0,1,0],"dist":[12.3,6.1,12.2,12.4,12.5,12.3,5.9,12.4],
 "fault":[0,0,0,0,0,0,0,0],"entry":"closed","exit":"closed",
 "calibrated":true,"free":6,"uptime":1234}
```
Sent on any change and every 1 s. `dist` = median cm or `null` if invalid. `entry`/`exit` ∈ `closed|opening|open|closing`.

```json
{"t":"gate_result","gate":"entry","ok":false,"reason":"full","req_id":"a1b2"}
```
Reply to every `gate` open command. `reason` ∈ `full|uncalibrated|busy|link`.

```json
{"t":"cal_result","ok":true,"baseline":[12.3,12.4,12.2,12.3,12.5,12.3,12.4,12.4],"failed":[]}
{"t":"cal_progress","done":7,"total":15}
```

### Server → ESP32

```json
{"t":"hello_ack"}
{"t":"hb"}
{"t":"gate","gate":"entry","action":"open","hold_ms":5000,"req_id":"a1b2"}
{"t":"gate","gate":"exit","action":"close"}
{"t":"cmd","cmd":"calibrate"}
```

### Server → browser (`/ws/ui`)

Full snapshot on connect and on every change (no diffs, it is tiny):

```json
{"t":"snapshot","ts":"2026-10-08T10:15:02+05:30",
 "esp32":{"online":true,"calibrated":true,"uptime":1234},
 "counts":{"total":8,"occupied":2,"available":6},
 "slots":[{"id":"G1","floor":"G","occupied":false,"car":null,"fault":false,"dist":12.3}],
 "cars":[{"car":1,"state":"PARKED","slot":"G2","entered_ts":"..."}],
 "gates":{"entry":"closed","exit":"closed"},
 "cameras":{"entry":{"state":"armed","last_read":{"car":3,"conf":0.91,"ts":"...","result":"approved"}},
            "exit":{"state":"cooldown","last_read":null}},
 "stats":{"entries_today":5,"exits_today":3,"peak_today":4},
 "events":[{"ts":"...","type":"entry","car":3,"slot":null,"detail":"approved"}]}
```

### Browser → server

```json
{"t":"gate","gate":"entry","action":"open"}
{"t":"cmd","cmd":"calibrate"}
{"t":"cmd","cmd":"reset_counters"}
{"t":"assign","slot":"G2","car":4}
```

---

## 8. Dashboard (browser)

Plain HTML/JS, responsive, works on laptop and phone browser on the same LAN.

```
┌──────────────────────────────────────────────────────────────┐
│ ParkTrack 360      ESP32: ● online     Calibrated ✔   10:15  │
├───────────────────────────────┬──────────────────────────────┤
│ First floor  [F1][F2][F3][F4] │  Entry camera (live + boxes) │
│ Ground floor [G1][G2][G3][G4] │  Last read: Car 3 ✔ approved │
│ Total 8  Occupied 2  Free 6   │  Exit camera (live + boxes)  │
│ Entry gate: closed  Exit: closed│ Last read: —               │
├───────────────────────────────┴──────────────────────────────┤
│ Stats: entries 5 | exits 3 | now 2 | peak 4 | per-car dwell  │
│ Controls: [Open entry][Close entry][Open exit][Close exit]   │
│           [Calibrate] [Reset counters]                       │
├──────────────────────────────────────────────────────────────┤
│ Event log (latest 50, newest first)                          │
└──────────────────────────────────────────────────────────────┘
```

- **[MUST]** Slot grid: 2 rows (First floor F1–F4 on top, Ground G1–G4 below), each tile green (vacant) or red (occupied) with the **car number**, "Unknown", or "Fault" (orange). Tiles turn grey with "stale" when the ESP32 is offline.
- **[MUST]** Counters: total, occupied, available; ESP32 online/offline indicator; calibrated indicator.
- **[MUST]** Gate status (entry/exit open/closed) and the last read per lane ROI with confidence and result (approved / denied + reason / unreadable + reason).
- **[MUST]** Entry and exit live panes with detection boxes, both sourced from the **same USB webcam stream**; each pane shows its corresponding ROI.
- **[MUST]** Event log (latest 50, newest first), colour-coded by type.
- **[MUST]** Stats: entries today, exits today, current and peak occupancy, per-car dwell time (table).
- **[MUST]** Controls: manual open/close each gate, **Calibrate** (with confirm dialog), reset counters (with confirm).
- **[SHOULD]** Click an "Unknown" or wrong tile to assign the correct car (1–8) from a dropdown, because car-in-slot is a heuristic.
- **[SHOULD]** Browser WebSocket auto-reconnect with back-off (1 s → 5 s) and a visible "reconnecting…" banner.
- **[COULD]** Small occupancy-over-time line chart (canvas, no libraries).
- LAN only, **no login in v1.x** [CONFIRM #7]. Anyone on the network can open gates; acceptable for a prototype, state this in the README.
- Target: dashboard reflects a slot change in **< 1 s**.

---

## 9. Repository layout and build order

```
parktrack360/
  README.md  requirements.txt  run_server.bat  run_server.sh  .gitignore
  firmware/
    parktrack360/            (folder name MUST equal sketch name)
      parktrack360.ino  config.h  secrets.example.h  sensors.* slots.* leds.*
      display.* gates.* net.* storage.* serial_cmd.*
    tests/
      t01_i2c_scan/  t02_hcsr04/  t03_leds/  t04_servo/  t05_gateleds/  t06_psram/
  server/   app.py  state.py  vision.py  db.py  config.yaml  static/ (index.html, app.js, style.css)
  vision/   train.py  train_colab.ipynb  data.yaml  dataset/
  tools/    collect.py  camera_probe.py  focus_test.py  roi_picker.py
            replay.py  benchmark.py  fake_esp32.py  make_tags.py
  tests/    test_state.py  test_protocol.py
  docs/     wiring.md  questions.md  step-1-report.md ...
```

`tools/make_tags.py` generates a printable A4 PDF/PNG with the digit labels 1–8 (2 copies each) at the exact size in 6.2.3.

`tools/fake_esp32.py` simulates the controller over WebSocket: connects, sends `state`, accepts `gate`, supports scripted scenarios (`park G1`, `leave G1`, `full`, `drop` to disconnect, `fault G3`).

### Build order (verify each step before the next; each has a Definition of Done)

| # | Step | Definition of Done |
|---|---|---|
| 1 | **Hardware checks** (`firmware/tests`): PSRAM check; I²C scan; read each HC-SR04 over serial; light every LED through both PCF8574s (walk 0xAA / 0x55 / 0xFF / 0x00 patterns); sweep each servo; toggle each gate LED pair | Owner pastes serial output; every device found/working; I²C addresses and OLED size recorded in `docs/wiring.md` |
| 2 | **Firmware standalone**: sensing, median/debounce, calibration, LEDs, OLED, gate state machine from serial commands | All serial commands work; all of acceptance tests 1, 2, 4 can be done without a laptop |
| 3 | **Server + dashboard** with `tools/fake_esp32.py` | `pytest` passes; full demo scenario runs on fake controller; dashboard latency < 1 s |
| 4 | **Link** real ESP32 ↔ server over WebSocket | Hello/state/gate round trip works; unplugging the network leaves gates closed (test 5) |
| 5 | **Single USB webcam + data collection** with `camera_probe`, `focus_test`, `roi_picker`, `collect.py`; labeling; training | One webcam passes the 6.2.2 focus/ROI checks; dataset meets 6.4 counts; model trained |
| 6 | **Vision integration** with stable-read rules and car logic | `replay.py` shows correct decisions on recorded clips; live approve/deny works |
| 7 | **Full acceptance test** (section 11) | Signed results sheet in `docs/acceptance.md` |

Firmware libraries: `Wire`, `Adafruit_GFX`, `Adafruit_SSD1306`, `ESP32Servo`, `WebSockets` (Markus Sattler), `ArduinoJson` (v7), `Preferences`, `WiFi`. Must compile in Arduino IDE 2.x with board **ESP32 Dev Module** and the latest stable Espressif core. List exact library versions used in `docs/wiring.md`.

---

## 10. Test data sheets (agent generates templates)

`docs/acceptance.md` contains blank tables for each test in section 11 with columns: attempt #, expected, observed, pass/fail, notes. Slot tests need 8 × 20 rows; car tests need 8 × 20 rows for each lane/ROI (entry and exit) using the same webcam.

---

## 11. Acceptance tests

1. All 16 slot LEDs, 4 gate LEDs, OLED and both servos operate as in sections 3–4 (checklist with the byte patterns of 3.4).
2. For each slot, 20 park/remove cycles with the real toy car: ≥ 95 % correct state, no flicker after debounce. Do this with the final mounting **before** vision work.
3. For each of the 8 cars, 20 passes through the entry ROI and 20 through the exit ROI: ≥ 95 % correct car ID, **zero wrong-ID gate opens**; unreadable cases keep the gate closed. Include negative trials: empty lane, a hand, a blank card, a tag with a different digit, two cars at once (must be denied as `conflict`), partially covered tag.
4. Full lot: entry denied, red entry LED, OLED shows PARKING FULL. Also verify the ESP32 refusal path by sending a manual entry-open from the dashboard when full.
5. Unplug the laptop network: gates close and stay closed, LEDs/OLED keep working. Reconnect: dashboard recovers without reflashing; car states preserved.
6. Dashboard latency (slot change → browser) < 1 s on the chosen network. Method: record a 60 fps phone video showing the car being placed and the dashboard; count frames from sensor LED change to dashboard change.
7. Server restart mid-session: car states and stats recover from SQLite; slot occupancy re-syncs within 2 s.
8. Calibration: with a car left in one slot the calibration is not silently accepted (the dialog warns; if the baseline is accepted, the occupied-slot test then fails visibly, so the procedure sheet says to empty the lot first). Calibration with an unplugged sensor reports that slot as failed.
9. Vision robustness: repeat test 3 at three light levels (room light, dim, strong lamp from the side) and with the camera nudged ~5 mm; accuracy must still be ≥ 90 % with zero wrong-ID opens.

---

## 12. Known risks and mitigations

| Risk | Mitigation |
|---|---|
| Toy cars are small with curved roofs; HC-SR04 echoes scatter | Mount ≥ 5 cm from roof, tune margin, use the end-wall mount fallback (3.5); verify test 2 early |
| 1 vs 7, 3 vs 8 confusion with hand-drawn digits | Printed tags (6.2.3), deliberate confusing samples, confusion matrix review |
| Cheap fixed-focus webcam is blurry at close range | Focus test, close-up lens, phone camera, or higher camera mount with bigger digits (6.2) |
| Training on one camera and demoing on another | Re-collect/fine-tune on the final camera |
| Autofocus drift | Lock focus (6.2.4) |
| Gate closes on a car because there is no passage sensor | Hold time 5 s, owner pushes the car promptly; **[COULD]** later add an IR break-beam |
| Car-to-slot association is a heuristic; wrong if two cars enter before either parks | Dashboard correction control; cap on concurrent `ENTERED` cars is not enforced in v1.x |
| GPIO15/GPIO2/GPIO5 boot-strap behaviour | Documented; no pin changes allowed without owner |
| College Wi-Fi blocks device-to-device traffic | Use network option A or B (2.1) |
| Brown-out during servo moves | Separate 5 V supply, bulk capacitor, gradual servo stepping |
| Demo failure from a wrong open | Stable-read rules (6.3) plus ESP32 refusals; manual dashboard override exists |

---

## 13. Open items [CONFIRM]

Resolved by the owner: 8 cars numbered 1–8; **one USB webcam shared by the entry and exit lanes**; dashboard shows car-in-slot; CPU inference on the laptop; build with Google Antigravity (no manual coding).

1. **Camera hardware:** **one USB webcam** is used for both entry and exit lanes. Confirm the planned mounting height and that both lanes fit in the webcam's field of view.
2. OLED resolution (128×64 assumed) and PCF8574 vs PCF8574A (I²C scan answers this).
3. Servo open/closed angles and hold time (defaults given).
4. Toy car heights (tallest and lowest) to set margin and mounting height; confirm sensor mount style (overhead or end-wall).
5. Training location: laptop NVIDIA GPU (CUDA) or Google Colab. (Owner has GPU support; confirm it is NVIDIA.)
6. Network option A, B or C (2.1) and the laptop IP.
7. Dashboard without login (LAN only).

---

## 14. Changes from v1.0 (owner review list)

Items 1–6 clarify or correct v1.0 and need the owner's OK; the rest only add detail.

1. **Sensing timing made consistent (4.1).** v1.0 asked for "median of 3 readings per cycle" and "3 consecutive cycles" and a "< 1 s" target; read literally that takes ≈ 1.4 s. v1.1 uses a *sliding* median of the latest 3 rounds plus 3-round debounce (≈ 0.5 s). Behaviour (median + debounce) is unchanged.
2. **ESP32 also refuses entry when uncalibrated or link is down** (4.4), in addition to "free slots = 0".
3. **Faulty sensors are counted as unavailable** and reported (4.1).
4. **Server rolls back an entry** if the ESP32 refuses it (5.1).
5. **Re-arm rule** (camera must see an empty lane for 1 s) added next to the 8 s cooldown (5.1).
6. **Firmware folder layout fixed**: `firmware/parktrack360/parktrack360.ino` (Arduino requires matching folder name).
7. Camera section simplified for the single USB webcam setup: one camera, two ROIs, focus/ROI validation, and no second camera requirement (6.2).
8. Printed tag recommendation, pixel-size rule, single-webcam MJPG configuration, `camera_probe`, `focus_test`, `roi_picker`.
9. Network options including the Windows Mobile Hotspot fixed-IP route; NVS overrides so no re-flash for network changes.
10. Full WebSocket schemas, SQLite schema, `config.yaml` and `config.h` templates, serial command set, build-step Definitions of Done, acceptance procedures, `fake_esp32` scenarios, unit-test requirement.
11. YOLO training settings: no horizontal/vertical flip, session-based split with held-out test set, ONNX/OpenVINO export for CPU.
12. Optional dashboard slot correction control, OLED link indicator flag, occupancy chart.

(v1.0 → pin map, wiring, active-LOW slot LEDs, one-GPIO-per-pair gate LEDs, buzzer removal: all unchanged.)

---

## Appendix A. Starter prompt for Antigravity

> Read `ParkTrack360_v1.1_Build_Spec.md` completely. It is the single source of truth. Follow section 0 rules. Start with Step 1 of section 9 only: create the test sketches in `firmware/tests/`, `docs/wiring.md`, and `docs/step-1-report.md` telling me exactly what to upload, what serial output to expect, and what to paste back. Do not change any pin, wiring or behaviour rule. If anything is unclear or looks wrong, write it in `docs/questions.md` and ask me. Do not start Step 2 until I confirm Step 1 results.

## Appendix B. Wiring verification checklist (owner, before power-on)

- [ ] All grounds common (external 5 V supply, ESP32, sensors, PCF8574s, servos, LED returns)
- [ ] Servo 5 V and sensor 5 V come from the external supply, not from the ESP32
- [ ] Every ECHO goes through 1 kΩ → junction (to ESP32) → 2 kΩ → GND
- [ ] PCF8574 and OLED powered from 3.3 V; SDA = 21, SCL = 22
- [ ] Slot LEDs: 3.3 V → 220 Ω → anode, cathode → PCF8574 pin
- [ ] Gate pair: green GPIO → 220 Ω → LED → GND; red 3.3 V → 220 Ω → LED → same GPIO
- [ ] Capacitor across servo 5 V rail
- [ ] Nothing on GPIO0/12; GPIO1 unconnected

## Appendix C. Troubleshooting quick table

| Symptom | Check |
|---|---|
| Upload fails with boot-mode error | Disconnect exit gate LED lead (GPIO2), retry; hold BOOT if the board has the button |
| I²C scan finds nothing | 3.3 V/GND, SDA/SCL swapped, no pull-ups |
| LED pattern inverted | PCF8574 is active-LOW here: 0 = ON |
| Sensor always reads 0 / timeout | ECHO divider, 5 V present, wrong pin |
| Slot flickers | Increase debounce, check side walls between sensors, margin too small |
| ESP32 cannot reach server | Same subnet, hotspot 2.4 GHz, Windows Firewall rule for port 8000, `server <ip> 8000` serial command |
| Single USB webcam image freezes | Use MJPG, verify the webcam driver/USB connection, and lower FPS if necessary |
| Digit read flickers 1↔7 | More training data, better lighting, printed tags |
| Gate moves jerky or ESP32 resets | Servo current, capacitor, shared ground |

---

## Appendix D. Full Physical Wiring Guide (Beginner-Friendly) + Verification Report

*Added after analysing `wiring_1.pdf` (the standalone wiring sheet) against this spec's own pin map (3.4) and behaviour rules (4). Section D.1 is a plain-English, do-this-then-this build walkthrough. Section D.2 is the verification/"simulation" pass — a dry-run check of every connection against ESP32 hardware facts and the numbers in this spec, done without power, before you ever plug anything in.*

### D.1 Before you touch a single wire

Four things decide whether this build works on the first try, and all four are mistakes that look fine until you power on:

1. **One shared ground.** Every GND pin in the whole system — ESP32, external 5 V supply, all 8 sensors, both PCF8574s, both servos, every LED cathode — must be electrically the same point. If even one is missed, you'll get ghost readings, flickering LEDs, or a servo that twitches randomly, and it will look like a totally different bug.
2. **Two separate power rails that share only ground.**
   - **5 V rail** (from the external 5 V/2 A adapter): feeds the 8 HC‑SR04 sensors and the 2 servos.
   - **3.3 V rail** (from the ESP32's own 3.3 V pin): feeds the OLED and both PCF8574 expanders.
   - The ESP32 itself is powered separately, from USB.
   - **Never** feed sensors or servos from the ESP32's 3.3 V/5V pin — the onboard regulator cannot supply the current a servo pulls when it moves (section 3.3 already budgets this: ~120 mA for all 8 sensors, up to ~1.3 A for a servo under stall).
3. **Every ECHO pin needs its own voltage divider.** HC‑SR04's ECHO output idles/pulses at 5 V; an ESP32 GPIO is only rated to 3.3 V. Skipping the divider on even one ECHO line risks killing that GPIO pin permanently. This is the single most common way to brick a hobbyist ESP32.
4. **Build and test in small stages**, not all 22 connections at once (see the step order in D.1.4). It is far easier to find one wrong wire among 3 than among 30.

#### D.1.1 Tools and parts checklist (from BOM in 3.2)
- Breadboard(s), jumper wires (M‑M, M‑F), a small Phillips screwdriver for the adapter terminal (if applicable)
- Multimeter (continuity/beep mode is essential — do not skip this)
- 8× HC‑SR04, 2× PCF8574 breakout, 1× SSD1306 OLED, 2× SG90/MG90S servo
- 16 slot LEDs (8 red + 8 green) + 4 gate LEDs (2 red + 2 green), 20× 220 Ω resistors
- 8× 1 kΩ + 8× 2 kΩ resistors (ECHO dividers — 16 resistors total)
- External 5 V/2 A supply, a 470–1000 µF electrolytic capacitor (servo rail smoothing)

#### D.1.2 Set up your two power rails first (no ESP32 connected yet)
1. Pick one breadboard row (or a strip of bus wire) as your **ground bus** — this single row will eventually touch every GND in the system.
2. Connect the external 5 V supply's **+** to a second bus row (**5 V rail**) and its **–** to the ground bus.
3. With the multimeter, confirm the 5 V rail actually reads ~5 V against the ground bus before connecting anything else to it.
4. Leave the ESP32's 3.3 V pin disconnected for now — you'll wire it to a third, separate bus (**3.3 V rail**) once the ESP32 is seated, and tie that 3.3 V rail's return to the same ground bus.

#### D.1.3 The ECHO voltage divider — built once, repeated 8 times
For **every** HC‑SR04, between its ECHO pin and the ESP32:
```
HC-SR04 ECHO ──[ 1 kΩ ]── • ──[ 2 kΩ ]── GND (ground bus)
                           │
                     ESP32 GPIO (this is the ECHO pin in the table below)
```
Why 1 kΩ then 2 kΩ: the two resistors form a divider that scales the sensor's 5 V pulse down to 5 V × (2 kΩ / (1 kΩ + 2 kΩ)) ≈ **3.33 V** — just inside the ESP32's 3.3 V input tolerance, with the ESP32 pin tapping the **middle junction**, not either end. TRIG does **not** need a divider: it's an input to the sensor, driven by the ESP32 at 3.3 V, which is above the HC‑SR04's ~2 V "high" threshold.

#### D.1.4 Recommended build order (test after each stage, before moving on)
1. **ESP32 alone.** Plug it into the laptop over USB, confirm the onboard LED lights and it shows up as a COM/serial port. Nothing else connected yet.
2. **I²C bus first: OLED + both PCF8574s.** Wire SDA→GPIO21 and SCL→GPIO22 to all three modules in parallel, power them from the ESP32's 3.3 V + the shared ground bus, set the PCF8574 address jumpers (0x20 and 0x21 — see D.1.5). Run an I²C scanner sketch before writing any display code; you should see `0x3C` (OLED) and `0x20`, `0x21`.
3. **One HC‑SR04 as a trial run.** Wire just slot G1 (TRIG→GPIO13, ECHO→divider→GPIO34), power it from the 5 V rail, and confirm you get a sane distance reading. Only once this works, wire the remaining 7.
4. **Slot LEDs through the PCF8574s.** Wire all 16 (8 red + 8 green), confirming the active‑LOW behaviour (writing a 0 to a pin turns its LED **on**).
5. **Gate indicator LEDs**, directly on ESP32 GPIO4 (entry pair) and GPIO2 (exit pair) — see the important discrepancy flagged in D.2.1 before wiring these.
6. **Servos last**, powered only from the external 5 V rail, with the smoothing capacitor across that rail near the servos. Confirm each gate sweeps smoothly before buttoning things up.
7. **Final continuity sweep** with the multimeter across every GND point (Appendix B's checklist), then full power‑on.

#### D.1.5 Complete pin-by-pin wiring tables

**8× HC‑SR04 ultrasonic sensors** — VCC → 5 V rail, GND → ground bus, for all eight:

| Slot | TRIG → ESP32 GPIO | ECHO → (1 kΩ/2 kΩ divider) → ESP32 GPIO | Note |
|---|---|---|---|
| G1 | 13 | 34 | ECHO pin is input‑only (fine — ECHO is always an input) |
| G2 | 14 | 35 | ECHO pin is input‑only |
| G3 | 27 | 36 | Silkscreened **VP**; input‑only |
| G4 | 26 | 39 | Silkscreened **VN**; input‑only |
| F1 | 25 | 18 | |
| F2 | 33 | 5 | GPIO5 is a boot‑strapping pin but is only *read* after boot — safe here |
| F3 | 32 | 17 | Silkscreened **TX2** |
| F4 | 19 | 16 | Silkscreened **RX2** |

**OLED (SSD1306, I²C)**

| OLED pin | Connects to |
|---|---|
| VCC | ESP32 **3.3 V** |
| GND | Ground bus |
| SDA | GPIO21 |
| SCL | GPIO22 |

**PCF8574 #1 — ground floor slot LEDs, address 0x20** and **PCF8574 #2 — first floor, address 0x21** (same wiring pattern, different address jumpers):

| PCF8574 pin | Connects to |
|---|---|
| VCC | ESP32 3.3 V (match this to the module's rated voltage) |
| GND | Ground bus |
| SDA | GPIO21 (shared bus) |
| SCL | GPIO22 (shared bus) |
| A0/A1/A2 | Jumpered for 0x20 (expander #1) or 0x21 (expander #2) |

| Slot | Green LED pin | Red LED pin |
|---|---|---|
| G1 (exp. 0x20) | P0 | P1 |
| G2 (exp. 0x20) | P2 | P3 |
| G3 (exp. 0x20) | P4 | P5 |
| G4 (exp. 0x20) | P6 | P7 |
| F1 (exp. 0x21) | P0 | P1 |
| F2 (exp. 0x21) | P2 | P3 |
| F3 (exp. 0x21) | P4 | P5 |
| F4 (exp. 0x21) | P6 | P7 |

Each slot LED: **PCF8574 pin → 220 Ω → LED anode → LED cathode → ground bus.** Because the PCF8574 can only sink current strongly (not source it), the firmware drives the pin **LOW to turn the LED on** — this is called "active‑LOW," and it is intentional, not a bug.

**2× Servo motors — entry/exit barrier gates** (signal = orange/yellow, VCC = red, GND = brown/black):

| Gate | Signal → ESP32 GPIO | VCC | GND |
|---|---|---|---|
| Entry | 23 | External 5 V rail | Ground bus |
| Exit | 15 | External 5 V rail | Ground bus |

Never power a servo from the ESP32 board itself. Put the 470–1000 µF capacitor across the 5 V rail close to the servos to absorb the current spike when they move.

**Gate indicator LEDs (complementary pair, one GPIO per gate)** — this spec's wiring, *not* the 4‑GPIO scheme in `wiring_1.pdf` (see D.2.1):

| Pair | GPIO | Wiring |
|---|---|---|
| Entry | 4 | green: GPIO4 → 220 Ω → green LED → ground bus. red: 3.3 V → 220 Ω → red LED → GPIO4 |
| Exit | 2 | green: GPIO2 → 220 Ω → green LED → ground bus. red: 3.3 V → 220 Ω → red LED → GPIO2 |

GPIO HIGH = green on/red off; GPIO LOW = red on/green off. One pin drives both LEDs of a pair in opposite directions — you are not missing a second wire per LED.

**No buzzer** — v1.1 removes it entirely (see D.2.2); GPIO1 stays unconnected and free for USB‑serial debugging.

### D.2 Verification pass ("paper simulation" — a dry run of the whole design before power‑on)

Because there's no live hardware in front of me to probe, I verified the design the way an engineer would on paper before a first power‑on: checked every GPIO assignment against confirmed ESP32 electrical behaviour, checked the two source documents against each other for contradictions, and re‑did the key arithmetic (divider voltage, current budget). Findings below — two are things you should resolve before wiring, the rest confirm the design is sound.

#### D.2.1 ⚠️ Conflict found: `wiring_1.pdf` disagrees with this spec on the gate LEDs

This is the most important finding — **follow this spec's version, not the PDF's**, and here's why:

| | `wiring_1.pdf` (older wiring sheet) | This spec, section 3.4 (source of truth per section 0, rule 1) |
|---|---|---|
| Gate LEDs | **4 separate GPIOs**: Entry Green=GPIO2, Entry Red=GPIO4, Exit Green=GPIO12, Exit Red=GPIO0 | **2 GPIOs, complementary pairs**: Entry pair=GPIO4, Exit pair=GPIO2 |
| Buzzer | Present, on GPIO1 | **Removed completely** (scope table, section 1) |

Two of the PDF's four gate-LED pins are actually unusable or risky on this exact board:
- **GPIO0 is not broken out on the 30‑pin ESP32 DevKit V1** at all (confirmed — this board exposes GPIO0 only via the BOOT button, not a header pin), so the PDF's "Exit Red → GPIO0" cannot physically be wired on this hardware.
- **GPIO12 is a strapping pin that sets the flash voltage at boot** — pulling it the wrong way at power‑on can make the board fail to boot or boot with a flash‑voltage mismatch, so this spec deliberately avoids it ("Unused... GPIO12 (avoid; boot strap)", section 3.4).

The PDF appears to be an earlier/alternate wiring sheet (also still including the buzzer, which v1.1 explicitly removed — section 1 and section 14, item 6 of this spec). **Wire the gate LEDs per the table in D.1.5 (GPIO4 entry pair, GPIO2 exit pair, complementary wiring), not per the PDF**, and leave the buzzer out entirely. Everything else in the PDF (sensor pins, OLED, PCF8574 addresses, servo pins, ECHO divider) matches this spec's section 3.4 exactly — those parts check out.

#### D.2.2 GPIO electrical facts, checked against ESP32 reference data

| Claim in this spec | Verified | Source |
|---|---|---|
| GPIO34/35/36(VP)/39(VN) are input‑only, with no internal pull‑up/down | ✅ Confirmed — these four pads have no output driver or internal pull resistors on the classic ESP32, which is exactly why they're only ever used for ECHO (always an input) and never TRIG | lastminuteengineers.com ESP32 pinout reference |
| GPIO0, 2, 5, 12, 15 are strapping pins needing care at boot | ✅ Confirmed — five strapping pins total | lastminuteengineers.com ESP32 pinout reference |
| GPIO0 is not exposed as a header pin on this 30‑pin board | ✅ Consistent with how this board family is documented — GPIO0 is only reachable via the onboard BOOT button on most 30‑pin DevKit V1 boards, matching this spec's note in 3.1 |
| GPIO5 is a strapping pin but safe here since it's only read after boot | ✅ Reasonable — GPIO5's strapping function only matters during the reset/boot window; once running it behaves as a normal input, which is all an ECHO pin needs |

#### D.2.3 Arithmetic re‑checked

- **ECHO divider output voltage:** 5 V × 2 kΩ ⁄ (1 kΩ + 2 kΩ) = **3.33 V** — just above the nominal 3.3 V but comfortably inside the ESP32's tolerance; matches the spec's claim.
- **Current budget on the 5 V/2 A supply:** 8 × HC‑SR04 (~15 mA each) ≈ 120 mA, plus one SG90‑class servo under stall (~1.3 A) if the two gates never move at exactly the same instant ≈ 1.42 A total, comfortably under 2 A. If your firmware ever opens both gates simultaneously, worst case ≈ 2 × 1.3 A + 0.12 A ≈ 2.72 A, which **would** exceed the supply — worth confirming the firmware never drives both servos at once, or upgrading the supply if it does.
- **GPIO count:** every pin used in section 3.4's pin map (22 GPIOs total: 8 TRIG + 8 ECHO + 2 I²C + 2 servo + 2 gate‑LED) is distinct — no two functions share a GPIO. This all checks out against the table in D.1.5.

#### D.2.4 What still needs a real multimeter/continuity check (can't be verified on paper)

- That your specific PCF8574 breakout modules are genuine PCF8574 (0x20–0x27) and not PCF8574A (0x38–0x3F) — confirm with an I²C scan, not by reading the silkscreen.
- That your OLED module is actually 0x3C and not 0x3D.
- Actual ground continuity across all the points listed in Appendix B — software/paper review cannot catch a loose jumper.
- Real servo stall current and brown‑out margin on your specific supply, under your specific cable gauge/length.

