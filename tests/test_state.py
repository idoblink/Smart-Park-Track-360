"""
ParkTrack 360 — tests/test_state.py
Unit tests for the parking state machine, vehicle transitions, and billing logic.
"""

import pytest
from pathlib import Path
from server.state import ParkingState
from server import db

@pytest.fixture
def test_state(tmp_path):
    test_db = tmp_path / "test_parktrack.db"
    test_config = tmp_path / "config.yaml"
    
    test_config.write_text("""
server: {host: 127.0.0.1, port: 8000}
esp32: {stale_after_s: 3, heartbeat_s: 1}
gate: {hold_ms: 5000, cooldown_s: 8, rearm_empty_s: 1.0}
entered_warn_s: 120
pricing:
  base_fee: 10.0
  hourly_rate: 20.0
  grace_period_min: 5.0
  currency: "INR"
""", encoding="utf-8")

    db.init_db(test_db)
    st = ParkingState(config_path=test_config, db_path=test_db)
    st.esp32_online = True
    st.esp32_calibrated = True
    return st, test_db

def test_initial_state(test_state):
    st, _ = test_state
    assert st.get_free_count() == 8
    assert st.get_occupied_count() == 0
    assert len(st.cars) == 8
    for car_id in range(1, 9):
        assert st.cars[car_id]["state"] == "OUTSIDE"

def test_entry_approval_and_duplicate_rejection(test_state):
    st, _ = test_state
    
    # Authorize Car 1
    ok, reason = st.authorize_entry(1)
    assert ok is True
    assert reason == "approved"
    assert st.cars[1]["state"] == "ENTERED"

    # Attempt to authorize Car 1 again -> Must fail (already inside)
    ok2, reason2 = st.authorize_entry(1)
    assert ok2 is False
    assert reason2 == "already_inside"

def test_slot_association_heuristic(test_state):
    st, _ = test_state
    
    # Car 2 enters
    st.authorize_entry(2)
    assert st.cars[2]["state"] == "ENTERED"

    # Slot G1 turns occupied via sensor
    st._handle_slot_transition("G1", is_occupied=True)
    assert st.slots["G1"]["occupied"] is True
    assert st.slots["G1"]["car"] == 2
    assert st.cars[2]["state"] == "PARKED"
    assert st.cars[2]["slot"] == "G1"

    # Slot G1 turns vacant via sensor
    st._handle_slot_transition("G1", is_occupied=False)
    assert st.slots["G1"]["occupied"] is False
    assert st.slots["G1"]["car"] is None
    assert st.cars[2]["state"] == "ENTERED"
    assert st.cars[2]["slot"] is None

def test_exit_and_fare_computation(test_state):
    st, _ = test_state
    
    # Car 3 enters and parks in F2
    st.authorize_entry(3)
    st._handle_slot_transition("F2", is_occupied=True)
    assert st.cars[3]["state"] == "PARKED"

    # Car 3 leaves via exit
    ok, reason, fare = st.authorize_exit(3)
    assert ok is True
    assert reason == "approved"
    assert st.cars[3]["state"] == "OUTSIDE"
    assert st.slots["F2"]["car"] is None

def test_full_lot_rejection(test_state):
    st, _ = test_state
    
    # Mark all 8 slots occupied
    for s_id in st.slot_ids:
        st.slots[s_id]["occupied"] = True
    
    assert st.get_free_for_entry() == 0

    # Car 4 attempts to enter
    ok, reason = st.authorize_entry(4)
    assert ok is False
    assert reason == "full"

def test_rollback_on_controller_refusal(test_state):
    st, _ = test_state
    
    # Car 5 authorized
    st.authorize_entry(5)
    assert st.cars[5]["state"] == "ENTERED"

    # Controller refused gate open
    st.rollback_entry(5, reason="gate_stuck")
    assert st.cars[5]["state"] == "OUTSIDE"

def test_tiered_pricing_structure(test_state):
    import datetime
    st, _ = test_state
    st.base_hours = 3.0
    st.base_fee = 50.0
    st.additional_hourly_rate = 20.0
    st.grace_period_min = 0.0

    now = datetime.datetime.now().astimezone()

    # Case 1: 30 minutes inside (within first 3 hours) -> ₹50.00
    ts_30m = (now - datetime.timedelta(minutes=30)).isoformat()
    _, fare_30m = st.compute_fare(ts_30m)
    assert fare_30m == 50.0

    # Case 2: Exactly 3 hours (180 minutes) inside -> ₹50.00
    ts_180m = (now - datetime.timedelta(minutes=180)).isoformat()
    _, fare_180m = st.compute_fare(ts_180m)
    assert fare_180m == 50.0

    # Case 3: 4 hours inside (1 extra hour) -> 50 + 1.0 * 20 = ₹70.00
    ts_240m = (now - datetime.timedelta(minutes=240)).isoformat()
    _, fare_240m = st.compute_fare(ts_240m)
    assert fare_240m == 70.0

    # Case 4: 4.5 hours inside (1.5 extra hours) -> 50 + 1.5 * 20 = ₹80.00
    ts_270m = (now - datetime.timedelta(minutes=270)).isoformat()
    _, fare_270m = st.compute_fare(ts_270m)
    assert fare_270m == 80.0

def test_unparked_car_free_exit(test_state):
    st, _ = test_state

    # Car 6 enters the facility
    ok, reason = st.authorize_entry(6)
    assert ok is True
    assert st.cars[6]["state"] == "ENTERED"
    assert st.cars[6]["has_parked"] is False

    # Car 6 never parks and reaches exit lane
    ok_free, reason_free, fare_free = st.authorize_exit_unparked(6)
    assert ok_free is True
    assert reason_free == "free_unparked_exit"
    assert fare_free == 0.0
    assert st.cars[6]["state"] == "OUTSIDE"

def test_parked_car_requires_payment_for_exit(test_state):
    st, _ = test_state
    st.grace_period_min = 0.0
    st.base_fee = 50.0

    # Car 7 enters and parks in G2
    st.authorize_entry(7)
    st._handle_slot_transition("G2", is_occupied=True)
    assert st.cars[7]["state"] == "PARKED"
    assert st.cars[7]["has_parked"] is True

    # Free unparked exit MUST be denied because it parked!
    ok_free, reason_free, _ = st.authorize_exit_unparked(7)
    assert ok_free is False
    assert reason_free == "car_has_parked_payment_required"

    # Paid exit succeeds
    ok_exit, reason_exit, fare = st.authorize_exit(7)
    assert ok_exit is True
    assert fare >= 50.0
    assert st.cars[7]["state"] == "OUTSIDE"
