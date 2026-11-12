"""
ParkTrack 360 — tests/test_qr_payment.py
End-to-end unit tests for QR scanning, Razorpay order creation, payment verification,
and entry/exit access control enforcement.
"""

import pytest
from fastapi.testclient import TestClient
from server.app import app, state

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_state():
    state.esp32_online = True
    state.esp32_calibrated = True
    state.base_hours = 3.0
    state.base_fee = 50.0
    state.additional_hourly_rate = 20.0
    state.grace_period_min = 0.0

    for c in range(1, 9):
        state.cars[c]["state"] = "OUTSIDE"
        state.cars[c]["slot"] = None
        state.cars[c]["entered_ts"] = None
        state.cars[c]["visit_id"] = None
        state.cars[c]["has_parked"] = False

    for s_id in state.slot_ids:
        state.slots[s_id]["occupied"] = False
        state.slots[s_id]["car"] = None


def test_active_cars_endpoint():
    # Initially no cars inside
    res = client.get("/api/active-cars")
    assert res.status_code == 200
    data = res.json()
    assert len(data["active_cars"]) == 0

    # Admit Car 1
    client.post("/api/entry", json={"car": 1})
    res2 = client.get("/api/active-cars")
    data2 = res2.json()
    assert len(data2["active_cars"]) == 1
    assert data2["active_cars"][0]["car"] == 1
    assert data2["active_cars"][0]["state"] == "ENTERED"


def test_qr_payment_order_creation():
    # Admit Car 2 and park in G1 via ultrasonic sensor
    client.post("/api/entry", json={"car": 2})
    state._handle_slot_transition("G1", is_occupied=True)
    assert state.cars[2]["has_parked"] is True

    # Generate QR order
    res = client.post("/api/payment/create-order", json={"car": 2})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["car"] == 2
    assert data["fare"] == 50.0
    assert "order_id" in data
    assert "upi_uri" in data
    assert "qr_code_image" in data
    assert data["qr_code_image"].startswith("data:image/png;base64,")


def test_payment_verification_unlocks_exit_gate():
    # Admit Car 3 and park in F1
    client.post("/api/entry", json={"car": 3})
    state._handle_slot_transition("F1", is_occupied=True)

    # Verify payment
    verify_res = client.post("/api/payment/verify", json={
        "car": 3,
        "razorpay_order_id": "order_test_123",
        "razorpay_payment_id": "pay_test_456",
        "method": "Razorpay UPI"
    })
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["ok"] is True
    assert v_data["gate_opened"] is True
    assert v_data["car"] == 3
    assert state.cars[3]["state"] == "OUTSIDE"
    assert state.gates["exit"] == "opening"


def test_unparked_car_free_pass():
    # Car 4 enters the lot
    client.post("/api/entry", json={"car": 4})
    assert state.cars[4]["state"] == "ENTERED"
    assert state.cars[4]["has_parked"] is False

    # Simulate exit for unparked car
    ok, reason, fare = state.authorize_exit_unparked(4)
    assert ok is True
    assert reason == "free_unparked_exit"
    assert fare == 0.0
    assert state.cars[4]["state"] == "OUTSIDE"


def test_exit_denied_for_outside_car():
    # Car 5 has never entered
    assert state.cars[5]["state"] == "OUTSIDE"

    # Attempt to verify payment / exit
    res = client.post("/api/payment/verify", json={"car": 5})
    assert res.status_code == 400

