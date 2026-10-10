"""
ParkTrack 360 — server/state.py
Central real-time state machine for parking slots, vehicles, barrier gates,
ESP32 link tracking, vision lane arming, and billing/fare computation.
"""

import time
import datetime
from typing import Dict, List, Optional, Any, Tuple
import yaml
from pathlib import Path
from server import db

CONFIG_PATH = Path("server/config.yaml")

class ParkingState:
    def __init__(self, config_path: Path = CONFIG_PATH, db_path: Path = db.DB_PATH):
        self.config = self._load_config(config_path)
        self.db_path = db_path
        
        # Timing thresholds
        self.stale_after_s = self.config.get("esp32", {}).get("stale_after_s", 3)
        self.cooldown_s = self.config.get("gate", {}).get("cooldown_s", 8)
        self.rearm_empty_s = self.config.get("gate", {}).get("rearm_empty_s", 1.0)
        self.entered_warn_s = self.config.get("entered_warn_s", 120)

        # Pricing config
        pricing = self.config.get("pricing", {})
        self.first_hour_fee = float(pricing.get("first_hour_fee", pricing.get("base_fee", 40.0)))
        self.additional_hourly_rate = float(pricing.get("additional_hourly_rate", pricing.get("hourly_rate", 20.0)))
        self.base_fee = self.first_hour_fee
        self.hourly_rate = self.additional_hourly_rate
        self.grace_period_min = float(pricing.get("grace_period_min", 0.0))
        self.currency = pricing.get("currency", "INR")

        # ESP32 link status
        self.esp32_online = False
        self.esp32_calibrated = False
        self.esp32_uptime = 0
        self.esp32_ip = "0.0.0.0"
        self.esp32_fw = "1.1.0"
        self.last_esp32_msg_ts = 0.0

        # Slot layout (indices 0..7)
        self.slot_ids = ["G1", "G2", "G3", "G4", "F1", "F2", "F3", "F4"]
        self.slots: Dict[str, Dict[str, Any]] = {}
        for s_id in self.slot_ids:
            self.slots[s_id] = {
                "id": s_id,
                "floor": s_id[0],
                "occupied": False,
                "car": None,
                "fault": False,
                "dist": None,
                "parking_id": None
            }

        # Gate statuses
        self.gates = {
            "entry": "closed",
            "exit": "closed"
        }

        # Lane camera read tracking
        self.cameras = {
            "entry": {
                "state": "armed", # armed, cooldown, unreadable
                "last_read": None,
                "cooldown_until": 0.0,
                "empty_since": time.time()
            },
            "exit": {
                "state": "armed",
                "last_read": None,
                "cooldown_until": 0.0,
                "empty_since": time.time()
            }
        }

        # Peak tracker
        self.peak_today = 0

        # Pending gate open request callbacks/IDs
        self.pending_gate_requests: Dict[str, Dict[str, Any]] = {}

        # Initialize DB and sync car states
        db.init_db(self.db_path)
        self.cars: Dict[int, Dict[str, Any]] = db.load_car_states(self.db_path)

    def _load_config(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def now_iso(self) -> str:
        return datetime.datetime.now().astimezone().isoformat()

    # --- ESP32 Telemetry Handling ---

    def handle_esp32_hello(self, fw: str, ip: str, calibrated: bool, reset_reason: str):
        self.esp32_online = True
        self.esp32_fw = fw
        self.esp32_ip = ip
        self.esp32_calibrated = calibrated
        self.last_esp32_msg_ts = time.time()
        db.log_event("esp32_connect", detail=f"IP={ip}, fw={fw}, reason={reset_reason}, cal={calibrated}", db_path=self.db_path)

    def handle_esp32_state(self, slots_data: List[int], dist_data: List[Optional[float]],
                           fault_data: List[int], entry_gate: str, exit_gate: str,
                           calibrated: bool, free_count: int, uptime: int):
        self.esp32_online = True
        self.esp32_calibrated = calibrated
        self.esp32_uptime = uptime
        self.last_esp32_msg_ts = time.time()

        self.gates["entry"] = entry_gate
        self.gates["exit"] = exit_gate

        # Update each slot
        for idx, s_id in enumerate(self.slot_ids):
            slot = self.slots[s_id]
            is_occupied = bool(slots_data[idx]) if idx < len(slots_data) else False
            is_fault = bool(fault_data[idx]) if idx < len(fault_data) else False
            dist = dist_data[idx] if idx < len(dist_data) else None

            old_occupied = slot["occupied"]
            slot["dist"] = dist
            slot["fault"] = is_fault

            if is_occupied != old_occupied:
                self._handle_slot_transition(s_id, is_occupied)

        # Update peak today
        current_occ = self.get_occupied_count()
        if current_occ > self.peak_today:
            self.peak_today = current_occ

    def _handle_slot_transition(self, slot_id: str, is_occupied: bool):
        slot = self.slots[slot_id]
        slot["occupied"] = is_occupied
        if is_occupied:
            # Slot became occupied -> Find oldest ENTERED car
            oldest_entered_car: Optional[int] = None
            oldest_ts: float = float("inf")
            
            for car_id, c_data in self.cars.items():
                if c_data["state"] == "ENTERED" and c_data.get("entered_ts"):
                    try:
                        dt = datetime.datetime.fromisoformat(c_data["entered_ts"]).timestamp()
                        if dt < oldest_ts:
                            oldest_ts = dt
                            oldest_entered_car = car_id
                    except Exception:
                        if oldest_entered_car is None:
                            oldest_entered_car = car_id

            if oldest_entered_car is not None:
                slot["car"] = oldest_entered_car
                c_info = self.cars[oldest_entered_car]
                c_info["state"] = "PARKED"
                c_info["slot"] = slot_id
                parking_id = db.start_parking(c_info.get("visit_id"), oldest_entered_car, slot_id, db_path=self.db_path)
                slot["parking_id"] = parking_id
                db.save_car_state(oldest_entered_car, "PARKED", slot_id, c_info.get("entered_ts"), c_info.get("visit_id"), db_path=self.db_path)
                db.log_event("slot_change", car=oldest_entered_car, slot=slot_id, detail="occupied", db_path=self.db_path)
            else:
                slot["car"] = None
                slot["parking_id"] = None
                db.log_event("slot_change", car=None, slot=slot_id, detail="occupied_unknown", db_path=self.db_path)
        else:
            # Slot became vacant
            car_id = slot["car"]
            if car_id is not None and car_id in self.cars:
                c_info = self.cars[car_id]
                c_info["state"] = "ENTERED"
                c_info["slot"] = None
                if slot.get("parking_id"):
                    db.end_parking(slot["parking_id"], db_path=self.db_path)
                    slot["parking_id"] = None
                db.save_car_state(car_id, "ENTERED", None, c_info.get("entered_ts"), c_info.get("visit_id"), db_path=self.db_path)
                db.log_event("slot_change", car=car_id, slot=slot_id, detail="vacated", db_path=self.db_path)
            else:
                db.log_event("slot_change", car=None, slot=slot_id, detail="vacated_unknown", db_path=self.db_path)
            slot["car"] = None
            slot["parking_id"] = None

    def check_link_liveness(self):
        now = time.time()
        if self.esp32_online and (now - self.last_esp32_msg_ts > self.stale_after_s):
            self.esp32_online = False
            db.log_event("esp32_disconnect", detail=f"No message for >{self.stale_after_s}s", db_path=self.db_path)

    # --- Metrics & Queries ---

    def get_free_count(self) -> int:
        return sum(1 for s in self.slots.values() if not s["occupied"] and not s["fault"])

    def get_occupied_count(self) -> int:
        return sum(1 for s in self.slots.values() if s["occupied"])

    def get_free_for_entry(self) -> int:
        entered_count = sum(1 for c in self.cars.values() if c["state"] == "ENTERED")
        return self.get_free_count() - entered_count

    # --- Billing & Fare Calculation ---

    def compute_fare(self, entered_ts_str: Optional[str]) -> Tuple[float, float]:
        """Calculates total dwell time in seconds and total fare in currency units.
        First hour (0..60m) = ₹40. Each additional hour = +₹20/hr (pro-rated by minute).
        """
        if not entered_ts_str:
            return 0.0, 0.0
        try:
            entered_dt = datetime.datetime.fromisoformat(entered_ts_str)
            now_dt = datetime.datetime.now().astimezone()
            duration_s = max(0.0, (now_dt - entered_dt).total_seconds())
            duration_min = duration_s / 60.0

            if self.grace_period_min > 0 and duration_min <= self.grace_period_min:
                return duration_s, 0.0

            if duration_min <= 60.0:
                total_fare = self.first_hour_fee
            else:
                additional_hours = (duration_min - 60.0) / 60.0
                total_fare = self.first_hour_fee + (additional_hours * self.additional_hourly_rate)

            return duration_s, round(total_fare, 2)
        except Exception:
            return 0.0, 0.0

    # --- Gate Authorization & Car Actions ---

    def authorize_entry(self, car_id: int) -> Tuple[bool, str]:
        """Evaluates entry lane authorization rules."""
        if car_id < 1 or car_id > 8:
            return False, "invalid_car"
        if not self.esp32_online:
            return False, "controller_offline"
        if not self.esp32_calibrated:
            return False, "uncalibrated"
        
        car = self.cars.get(car_id)
        if not car or car["state"] != "OUTSIDE":
            return False, "already_inside"
        
        if self.get_free_for_entry() <= 0:
            return False, "full"

        # Approve entry
        now_str = self.now_iso()
        visit_id = db.start_visit(car_id, db_path=self.db_path)
        car["state"] = "ENTERED"
        car["entered_ts"] = now_str
        car["visit_id"] = visit_id
        car["slot"] = None
        db.save_car_state(car_id, "ENTERED", None, now_str, visit_id, db_path=self.db_path)
        db.log_event("entry", car=car_id, detail="approved", db_path=self.db_path)

        # Arm camera cooldown
        self.cameras["entry"]["cooldown_until"] = time.time() + self.cooldown_s
        self.cameras["entry"]["state"] = "cooldown"
        return True, "approved"

    def rollback_entry(self, car_id: int, reason: str):
        car = self.cars.get(car_id)
        if car and car["state"] == "ENTERED":
            car["state"] = "OUTSIDE"
            car["entered_ts"] = None
            car["visit_id"] = None
            db.save_car_state(car_id, "OUTSIDE", None, None, None, db_path=self.db_path)
            db.log_event("deny", car=car_id, detail=f"rollback: {reason}", db_path=self.db_path)

    def authorize_exit(self, car_id: int) -> Tuple[bool, str, float]:
        """Evaluates exit lane authorization and calculates final bill."""
        if car_id < 1 or car_id > 8:
            return False, "invalid_car", 0.0
        
        car = self.cars.get(car_id)
        if not car or car["state"] == "OUTSIDE":
            return False, "not_inside", 0.0

        # Compute dwell time and bill
        inside_s, fare = self.compute_fare(car.get("entered_ts"))

        # Clear slot if still associated
        if car.get("slot"):
            s_id = car["slot"]
            if s_id in self.slots:
                self.slots[s_id]["car"] = None
                if self.slots[s_id].get("parking_id"):
                    db.end_parking(self.slots[s_id]["parking_id"], db_path=self.db_path)
                    self.slots[s_id]["parking_id"] = None

        visit_id = car.get("visit_id")
        if visit_id:
            db.close_visit(visit_id, inside_s=inside_s, parked_s=inside_s, fare=fare, db_path=self.db_path)

        car["state"] = "OUTSIDE"
        car["slot"] = None
        car["entered_ts"] = None
        car["visit_id"] = None
        db.save_car_state(car_id, "OUTSIDE", None, None, None, db_path=self.db_path)
        db.log_event("exit", car=car_id, detail=f"fare={fare} {self.currency}", db_path=self.db_path)

        self.cameras["exit"]["cooldown_until"] = time.time() + self.cooldown_s
        self.cameras["exit"]["state"] = "cooldown"
        return True, "approved", fare

    def manual_assign_slot(self, slot_id: str, car_id: Optional[int]):
        """Operator manual correction of car in slot."""
        if slot_id not in self.slots:
            return False
        slot = self.slots[slot_id]
        
        # If removing existing car
        old_car = slot["car"]
        if old_car and old_car in self.cars:
            self.cars[old_car]["state"] = "ENTERED"
            self.cars[old_car]["slot"] = None
            db.save_car_state(old_car, "ENTERED", None, self.cars[old_car].get("entered_ts"), self.cars[old_car].get("visit_id"), db_path=self.db_path)

        if car_id is not None and 1 <= car_id <= 8:
            c_info = self.cars[car_id]
            c_info["state"] = "PARKED"
            c_info["slot"] = slot_id
            slot["car"] = car_id
            slot["occupied"] = True
            db.save_car_state(car_id, "PARKED", slot_id, c_info.get("entered_ts"), c_info.get("visit_id"), db_path=self.db_path)
            db.log_event("slot_change", car=car_id, slot=slot_id, detail="manual_assigned", db_path=self.db_path)
        else:
            slot["car"] = None
            db.log_event("slot_change", car=None, slot=slot_id, detail="manual_cleared", db_path=self.db_path)
        return True

    # --- UI Snapshot Serialization ---

    def get_snapshot(self) -> Dict[str, Any]:
        """Constructs full UI snapshot conforming to section 7.4 of spec."""
        stats = db.get_stats(db_path=self.db_path)
        
        slots_list = []
        for s_id in self.slot_ids:
            s = self.slots[s_id]
            slots_list.append({
                "id": s["id"],
                "floor": s["floor"],
                "occupied": s["occupied"],
                "car": s["car"],
                "fault": s["fault"],
                "dist": s["dist"]
            })

        cars_list = []
        for c_id in range(1, 9):
            c = self.cars[c_id]
            dwell_s, fare = self.compute_fare(c.get("entered_ts"))
            cars_list.append({
                "car": c_id,
                "state": c["state"],
                "slot": c["slot"],
                "entered_ts": c["entered_ts"],
                "dwell_s": round(dwell_s, 0) if c["state"] != "OUTSIDE" else 0,
                "current_fare": fare if c["state"] != "OUTSIDE" else 0.0
            })

        return {
            "t": "snapshot",
            "ts": self.now_iso(),
            "esp32": {
                "online": self.esp32_online,
                "calibrated": self.esp32_calibrated,
                "uptime": self.esp32_uptime,
                "ip": self.esp32_ip,
                "fw": self.esp32_fw
            },
            "counts": {
                "total": 8,
                "occupied": self.get_occupied_count(),
                "available": self.get_free_count()
            },
            "pricing": {
                "first_hour_fee": self.first_hour_fee,
                "additional_hourly_rate": self.additional_hourly_rate,
                "base_fee": self.base_fee,
                "hourly_rate": self.hourly_rate,
                "grace_period_min": self.grace_period_min,
                "currency": self.currency
            },
            "slots": slots_list,
            "cars": cars_list,
            "gates": self.gates,
            "cameras": {
                "entry": {
                    "state": self.cameras["entry"]["state"],
                    "last_read": self.cameras["entry"]["last_read"]
                },
                "exit": {
                    "state": self.cameras["exit"]["state"],
                    "last_read": self.cameras["exit"]["last_read"]
                }
            },
            "stats": {
                "entries_today": stats["entries_today"],
                "exits_today": stats["exits_today"],
                "peak_today": self.peak_today,
                "epoch_ts": stats["epoch_ts"]
            },
            "events": db.get_recent_events(limit=50, db_path=self.db_path)
        }
