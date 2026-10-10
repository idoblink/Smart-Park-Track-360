# PCF8574 (HW-61) LED Expander Wiring & "Black Part" Guide

This guide provides beginner-friendly, step-by-step wiring instructions for using the **PCF8574 (HW-61 I2C LCD Backpack)** modules as 8-channel LED drivers for the ParkTrack 360 parking system.

---

## ⚡ Live Operating Behavior (No Calibration Needed)

The firmware is configured to operate immediately upon boot:
* **Distance > 2.5 cm (Empty slot / background distance):**
  - Corresponding slot LED turns **GREEN** (Vacant).
* **Distance ≤ 2.5 cm (Hand or model vehicle placed in slot):**
  - Corresponding slot LED turns **RED** (Occupied).
* **16×2 LCD Screen:**
  - Line 0: ` SMART PARKING`
  - Line 1: `Occ:0  Free:8` (Dynamically updates, e.g. `Occ:1  Free:7` when a hand/car is placed in any slot).
  - Displays ` PARKING FULL` when all 8 slots are occupied.

---

## 1. Visual Map of the PCF8574 (HW-61) Board

Look at your HW-61 board with the 16-pin row along the top and the 4-pin row at the bottom:

```text
 ╔═══════════════════════════════════════════════════════════════════════════════════╗
 ║                         TOP 16-PIN HEADER (PINS 1 TO 16)                          ║
 ║  [ 1]  [ 2]  [ 3] │ [ 4]  [ 5]  [ 6] │ [ 7]  [ 8]  [ 9] [10] │ [11] [12] [13] [14] ║
 ║  VSS   VDD   V0   │  RS   RW    E    │  D0   D1   D2   D3   │  D4   D5   D6   D7   ║
 ║  (GND) (5V)       │ (P0) (P1)  (P2)  │ (EMPTY / DISCONNECTED) │ (P4) (P5) (P6) (P7)  ║
 ║  ─── SKIP ───     │ ───────┬──────── │ ────── SKIP ────────── │ ────────┬─────────── ║
 ║                   │        │         │                        │         │            ║
 ║  [A0] [A1] [A2]   │        │         │       ┌─────────┐      │         │            ║
 ║  Address Pads     │        │         │       │  BLUE   │      │   2-PIN BLACK JUMPER ║
 ║  (Solder Bridge)  │        │         │       │  KNOB   │      │   ┌────────┐         ║
 ║                   │        │                 └─────────┘      │   │ [1][2] │ "LED"   ║
 ║                   │        │        PCF8574                   │   └────────┘         ║
 ║                   │        │        MAIN IC                   │    (Cap pulls off!)  ║
 ║                   │        │                                  │                      ║
 ║       [GND]     [VCC]    [SDA]    [SCL]                       │                      ║
 ║         │         │        │        │                         │                      ║
 ╚═════════╪═════════╪════════╪════════╪═════════════════════════╪══════════════════════╝
           │         │        │        │                         │
        Breadboard Breadboard ESP32  ESP32                       │
           GND       +5V     GPIO 21 GPIO 22                     │
```

---

## 2. What Is the "Top Black Part" & What Do I Do With It?

On the HW-61 board, beginners typically notice two different black components:
1. **The 2-Pin Black Jumper (Small rectangular black plastic block labeled "LED")**
2. **The 16-Pin Long Black Header Strip (Row of 16 pins along the edge)**

Below is the exact explanation and connection instructions for both:

---

### Part A: The 2-Pin Black Jumper Block (Labeled "LED")

#### 1. What is it?
On a standard LCD display, this 2-pin header holds a small black plastic cap (called a *jumper shunt*). When plugged in, it supplies power to the LCD screen backlight. 

On this module, **Pin P3 of the PCF8574 chip controls an on-board NPN transistor (marked Q1)** that switches this header to ground!

#### 2. What do you do with it?
1. **Grip the little black plastic cap with your fingers and pull it straight UP and off.** Store the black cap in your toolbox.
2. Underneath, you will see **two bare metal pins**:
   * **Pin 1 (closer to the board edge):** Permanently connected to +5V (Do NOT use this pin).
   * **Pin 2 (closer to the blue knob / transistor):** This is the **switched Ground (P3)** pin!
3. **Connect a Female-to-Male jumper wire** onto **Pin 2**:
   * The **Female end** slips directly over Pin 2.
   * The **Male end** plugs into your breadboard row with the **Slot 2 Red LED Resistor** (G2 Red on Ground Floor, F2 Red on First Floor).

#### Circuit Diagram for the 2-Pin Black Jumper (Slot 2 Red LED):

```mermaid
flowchart LR
    A["Breadboard +5V Rail"] -->|Long Leg (+)| B["Slot 2 Red LED"]
    B -->|Short Leg (-)| C["220Ω Resistor"]
    C -->|Jumper Wire| D["Pin 2 on 2-Pin Header<br/>(Switched Pin)"]
    subgraph HW-61 Module Circuit
        D --> E["Internal NPN Transistor (Q1)"]
        F["PCF8574 Pin P3"] -->|Base Control| E
        E --> G["GND (Breadboard Ground Bus)"]
    end
```

* **When Slot 2 is OCCUPIED:** The ESP32 tells the PCF8574 to activate the transistor $\rightarrow$ Pin 2 connects to GND $\rightarrow$ Red LED lights up!
* **When Slot 2 is VACANT:** The transistor stays OFF $\rightarrow$ Red LED turns off.

---

### Part B: The 16-Pin Long Black Header Strip

This 16-pin connector is where all the other Slot LEDs connect. 

#### Critical Beginner Rules for Counting Pins 1 to 16:
* **Pin 1 is on the far left** (nearest the address solder pads A0, A1, A2).
* **Pin 16 is on the far right** (nearest the 2-pin black jumper).

| Pin # | Silk Label | Can I use it for an LED? | Why? |
| :---: | :---: | :---: | :--- |
| **Pin 1** | VSS | ❌ **DO NOT USE** | Hardwired directly to GND on the PCB. If you plug an LED here, it stays ON forever! |
| **Pin 2** | VDD | ❌ **DO NOT USE** | Hardwired directly to +5V on the PCB. |
| **Pin 3** | V0 | ❌ **DO NOT USE** | Connected to the blue contrast knob. |
| **Pin 4** | **RS** | ✅ **USE: Slot 1 Green** | Controlled by internal pin P0 |
| **Pin 5** | **RW** | ✅ **USE: Slot 1 Red** | Controlled by internal pin P1 |
| **Pin 6** | **E** | ✅ **USE: Slot 2 Green** | Controlled by internal pin P2 |
| **Pin 7** | D0 | ❌ **DO NOT USE** | **Blank / Disconnected on PCB!** (No trace leads here) |
| **Pin 8** | D1 | ❌ **DO NOT USE** | **Blank / Disconnected on PCB!** |
| **Pin 9** | D2 | ❌ **DO NOT USE** | **Blank / Disconnected on PCB!** |
| **Pin 10**| D3 | ❌ **DO NOT USE** | **Blank / Disconnected on PCB!** |
| **Pin 11**| **D4** | ✅ **USE: Slot 3 Green** | Controlled by internal pin P4 |
| **Pin 12**| **D5** | ✅ **USE: Slot 3 Red** | Controlled by internal pin P5 |
| **Pin 13**| **D6** | ✅ **USE: Slot 4 Green** | Controlled by internal pin P6 |
| **Pin 14**| **D7** | ✅ **USE: Slot 4 Red** | Controlled by internal pin P7 |
| **Pin 15**| BLA | ❌ **DO NOT USE** | Backlight Anode |
| **Pin 16**| BLK | ❌ **DO NOT USE** | Backlight Cathode |

> **Key takeaway:** You **SKIP pins 1, 2, 3** and you **SKIP pins 7, 8, 9, 10**.  
> The 7 usable LED pins on the 16-pin row are **4, 5, 6, 11, 12, 13, 14**.  
> The 8th LED pin is the **2-pin black jumper (Pin 2)** described in Part A.

---

## 3. General LED Wiring Pattern (Active-LOW)

Every single LED in the system follows the exact same 3-step circuit:

```mermaid
flowchart LR
    Rail["Breadboard +5V Rail"] -->|Long Leg (+)| LED["LED Anode"]
    LED -->|Short Leg (-)| Res["220Ω Resistor"]
    Res -->|Jumper Wire| PCF["PCF8574 Pin (Sinks to GND when ON)"]
```

1. **Long leg (+) of the LED** ➔ Breadboard **5V Rail**
2. **Short leg (-) of the LED** ➔ Breadboard empty row
3. **Resistor Leg 1** ➔ Same row as the LED short leg
4. **Resistor Leg 2** ➔ Plugs into the specific PCF8574 pin

---

## 4. Complete Step-by-Step Connection Tables

### Ground Floor Board (Address `0x26` — Solder Bridge on A0)

| Parking Slot & Color | LED (+) Anode | LED (-) Cathode & Resistor | Target PCF8574 Pin |
| :--- | :--- | :--- | :--- |
| **Slot G1 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 4 (RS / P0)** |
| **Slot G1 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 5 (RW / P1)** |
| **Slot G2 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 6 (E / P2)** |
| **Slot G2 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **2-Pin Black Jumper (Pin 2 / P3)** *(Cap removed)* |
| **Slot G3 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 11 (D4 / P4)** |
| **Slot G3 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 12 (D5 / P5)** |
| **Slot G4 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 13 (D6 / P6)** |
| **Slot G4 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 14 (D7 / P7)** |

---

### First Floor Board (Address `0x25` — Solder Bridge on A1)

| Parking Slot & Color | LED (+) Anode | LED (-) Cathode & Resistor | Target PCF8574 Pin |
| :--- | :--- | :--- | :--- |
| **Slot F1 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 4 (RS / P0)** |
| **Slot F1 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 5 (RW / P1)** |
| **Slot F2 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 6 (E / P2)** |
| **Slot F2 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **2-Pin Black Jumper (Pin 2 / P3)** *(Cap removed)* |
| **Slot F3 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 11 (D4 / P4)** |
| **Slot F3 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 12 (D5 / P5)** |
| **Slot F4 Green** | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 13 (D6 / P6)** |
| **Slot F4 Red**   | Breadboard 5V Rail | 220Ω Resistor | ➔ **Header Pin 14 (D7 / P7)** |

---

## 5. Verification With `ledtest`

Once all resistors are plugged into the correct pins:
1. Open the Arduino Serial Monitor at **115200 baud**.
2. Type `ledtest` and press **Enter**.
3. The ESP32 will test every single LED one by one:
   * Slot 1 Green $\rightarrow$ Slot 1 Red
   * Slot 2 Green $\rightarrow$ Slot 2 Red (tests the black jumper pin!)
   * Slot 3 Green $\rightarrow$ Slot 3 Red
   * Slot 4 Green $\rightarrow$ Slot 4 Red
4. If an LED does not turn on:
   * Check that its long leg (+) is in the **5V power rail**.
   * Check that you didn't accidentally plug into Pins 1–3 or 7–10.
