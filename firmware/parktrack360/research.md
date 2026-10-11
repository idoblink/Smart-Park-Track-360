# ParkTrack 360 Firmware — Bug Research & Fix Log

**Date:** 2026-10-10  
**Scope:** Complete code audit of all `.cpp`, `.h`, and `.ino` files  
**Issues reported by user:** Display shows minute errors, LEDs always red, threshold should be 2.5 cm

---

## Bug #1: OCCUPIED_THRESHOLD_CM is 5.0 cm — Should be 2.5 cm

**File:** `config.h` line 55  
**Current value:** `#define OCCUPIED_THRESHOLD_CM 5.0f`  
**Required value:** `#define OCCUPIED_THRESHOLD_CM 2.5f`  

**Impact:** With threshold at 5.0 cm, any object within 5 cm triggers OCCUPIED. User wants 2.5 cm.

**Also affects:**
- `slots.cpp` line 29: `if (dist <= OCCUPIED_THRESHOLD_CM)` — uses this threshold correctly via the macro.
- `slots.cpp` line 34: `if (_baseline[slot] > 5.0f ...)` — this has a **hardcoded 5.0f** that should also use the macro.
- `slots.cpp` line 63: print log says `<= 5.0 cm = OCCUPIED` — should say 2.5 cm.
- `pcf8-connect.md` line 10-11: documentation references `> 5.0 cm` and `<= 5.0 cm`.

**Fix:** Change `OCCUPIED_THRESHOLD_CM` to `2.5f`. Also fix the hardcoded `5.0f` in `slots.cpp` classify() to use the macro. Update display/log strings.

---

## Bug #2: LEDs Always Red — Root Cause Analysis

**File:** `leds.cpp` lines 70-121, `slots.cpp` lines 44-65  

### Root Cause Found

The user reports LEDs are **always red**, meaning all slots are classified as OCCUPIED.

Tracing through the code:

1. On boot, `slots.cpp` line 47 forces `_calibrated = true` regardless of NVS state
2. Baselines are loaded from NVS with default of **30.0 cm** (line 50)
3. If user never ran calibration, all baselines are 30 cm
4. In `classify()` (lines 24-39), the baseline comparison:
   ```cpp
   if (_baseline[slot] > 5.0f && dist < (_baseline[slot] - _margin)) {
       return SLOT_OCCUPIED;
   }
   ```
5. With baseline=30 cm and margin=1.5 cm: anything below **28.5 cm** = OCCUPIED
6. **Result: Any sensor reading under 28.5 cm triggers OCCUPIED → all LEDs red**

This is the core bug. The default baselines of 30 cm are completely wrong for an uncalibrated system, and the baseline comparison should NOT be used when the system hasn't been properly calibrated.

### Fix:
1. Track whether NVS actually had real calibration data (`_nvsCalibrated`)
2. Only apply baseline comparison in `classify()` when `_nvsCalibrated` is true
3. When NOT calibrated via NVS, rely solely on the simple proximity threshold (`dist <= OCCUPIED_THRESHOLD_CM`)
4. This means uncalibrated slots: distance > 2.5 cm = VACANT (green), distance <= 2.5 cm = OCCUPIED (red)

---

## Bug #3: Display "Minute Errors"

**File:** `display.cpp` lines 62-89  

The display shows wrong Occ/Free counts because Bug #2 makes ALL slots show as OCCUPIED. With all 8 slots wrongly occupied:
- Display shows `Occ:8  Free:0` or ` PARKING FULL` when the lot is actually empty
- User sees these as "minute errors" — the counts are simply wrong

**Fix:** Resolving Bug #2 automatically fixes this. The display code itself is correct.

---

## Bug #4: Default baselines wrong for uncalibrated system

**File:** `slots.cpp` lines 47-50  
```cpp
_calibrated = true;  // forced on boot
_baseline[i] = Storage::loadBaseline(i, 30.0f);  // default 30cm if never calibrated
```

The forced `_calibrated = true` + default 30cm baselines creates the cascade failure described in Bug #2.

**Fix:** Store NVS calibration state separately and gate the baseline comparison on it.

---

## Bug #5: Hardcoded 5.0f in classify()

**File:** `slots.cpp` line 34  
```cpp
if (_baseline[slot] > 5.0f && ...)
```

Should use `OCCUPIED_THRESHOLD_CM` macro for consistency and maintainability.

**Fix:** Replace `5.0f` with `OCCUPIED_THRESHOLD_CM`.

---

## Summary of All Changes

| File | Line(s) | Change |
|------|---------|--------|
| `config.h` | 55 | `OCCUPIED_THRESHOLD_CM` 5.0f → 2.5f |
| `slots.cpp` | 19 | Add `_nvsCalibrated` state variable |
| `slots.cpp` | 24-39 | Fix classify() — only use baseline when NVS calibrated; use macro not 5.0f |
| `slots.cpp` | 46-47 | Track `_nvsCalibrated` from NVS load |
| `slots.cpp` | 63 | Update log message to reflect 2.5 cm threshold |

## Files NOT Changed (No bugs found)
- `parktrack360.ino` — Main sketch, initialization order correct
- `display.cpp` / `display.h` — Display logic correct, counts depend on slot logic
- `leds.cpp` / `leds.h` — Active-LOW logic correct, bit mapping correct, P3 transistor behavior consistent
- `sensors.cpp` / `sensors.h` — Sensor reading, median filtering, round-robin correct
- `gates.cpp` / `gates.h` — Servo state machine correct
- `comm.cpp` / `comm.h` — JSON comms correct
- `serial_cmd.cpp` / `serial_cmd.h` — CLI commands correct
- `storage.cpp` / `storage.h` — NVS persistence correct

## Status: ALL FIXES APPLIED ✓
