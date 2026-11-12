"""
ParkTrack 360 — tests/test_phonepe.py
Unit tests for PhonePe integration, order creation, checksum signing,
webhook processing, and automatic exit barrier gate opening.
"""

import base64
import json
import hashlib
import pytest
from fastapi.testclient import TestClient

from server.app import app, state, phonepe_client
from server.phonepe import PhonePeClient

@pytest.fixture(autouse=True)
def reset_parking_state():
    state.cars.clear()
    for cid in range(1, 9):
        state.cars[cid] = {
            "state": "OUTSIDE",
            "entered_ts": None,
            "slot": None,
            "has_parked": False
        }
    state.gates["entry"] = "closed"
    state.gates["exit"] = "closed"
    state.car_at_exit = None

def test_phonepe_checksum_generation():
    client = PhonePeClient(state.config)
    payload_str = "eyJ0ZXN0IjoxMjN9"
    endpoint = "/pg/v1/pay"
    checksum = client._compute_checksum(payload_str, endpoint)
    assert "###" in checksum
    assert checksum.endswith("###1")
    
    # Verify sha256 computation
    expected_hash = hashlib.sha256(f"{payload_str}{endpoint}{client.salt_key}".encode("utf-8")).hexdigest()
    assert checksum.startswith(expected_hash)

def test_phonepe_webhook_verification():
    client = PhonePeClient(state.config)
    sample_payload = {"code": "PAYMENT_SUCCESS", "data": {"merchantTransactionId": "PT360_CAR_3_12345"}}
    payload_b64 = base64.b64encode(json.dumps(sample_payload).encode("utf-8")).decode("utf-8")
    
    valid_hash = hashlib.sha256(f"{payload_b64}{client.salt_key}".encode("utf-8")).hexdigest()
    x_verify = f"{valid_hash}###1"
    
    assert client.verify_webhook_checksum(payload_b64, x_verify) is True
    assert client.verify_webhook_checksum(payload_b64, "invalid_hash###1") is False

def test_phonepe_create_order_active_car():
    tc = TestClient(app)
    # Put Car #3 inside
    state.cars[3]["state"] = "PARKED"
    state.cars[3]["slot"] = "G1"
    state.cars[3]["has_parked"] = True
    state.cars[3]["entered_ts"] = "2026-11-12T10:00:00"

    resp = tc.post("/api/payment/phonepe/create-order", json={"car": 3, "phone": "9876543210"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["provider"] == "phonepe"
    assert data["car"] == 3
    assert data["fare"] >= 50.0
    assert "payment_url" in data
    assert "txn_id" in data

def test_phonepe_create_order_outside_car_rejected():
    tc = TestClient(app)
    # Car #4 is outside
    resp = tc.post("/api/payment/phonepe/create-order", json={"car": 4})
    assert resp.status_code == 400
    assert "not inside facility" in resp.json()["detail"]

def test_phonepe_status_success_auto_opens_gate(monkeypatch):
    tc = TestClient(app)
    # Put Car #2 inside facility and parked
    state.cars[2]["state"] = "PARKED"
    state.cars[2]["slot"] = "G2"
    state.cars[2]["has_parked"] = True
    state.cars[2]["entered_ts"] = "2026-11-12T10:00:00"
    state.car_at_exit = 2

    # Mock phonepe_client.check_payment_status to return paid
    def mock_check_status(txn_id):
        return {
            "ok": True,
            "code": "PAYMENT_SUCCESS",
            "is_paid": True,
            "is_pending": False,
            "message": "Payment Successful",
            "txn_id": txn_id
        }

    monkeypatch.setattr(phonepe_client, "check_payment_status", mock_check_status)

    resp = tc.get("/api/payment/phonepe/status/2/PT360_CAR_2_999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["is_paid"] is True
    assert data["gate_opened"] is True
    assert state.gates["exit"] == "opening"
    assert state.cars[2]["state"] == "OUTSIDE"

def test_phonepe_callback_webhook_auto_opens_gate():
    tc = TestClient(app)
    # Put Car #5 inside
    state.cars[5]["state"] = "PARKED"
    state.cars[5]["slot"] = "F1"
    state.cars[5]["has_parked"] = True
    state.cars[5]["entered_ts"] = "2026-11-12T10:00:00"

    webhook_payload = {
        "code": "PAYMENT_SUCCESS",
        "data": {
            "merchantTransactionId": "PT360_CAR_5_123456",
            "amount": 5000
        }
    }
    payload_b64 = base64.b64encode(json.dumps(webhook_payload).encode("utf-8")).decode("utf-8")
    client = PhonePeClient(state.config)
    valid_hash = hashlib.sha256(f"{payload_b64}{client.salt_key}".encode("utf-8")).hexdigest()
    x_verify = f"{valid_hash}###1"

    resp = tc.post(
        "/api/payment/phonepe/callback",
        json={"response": payload_b64},
        headers={"x-verify": x_verify}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert state.gates["exit"] == "opening"
    assert state.cars[5]["state"] == "OUTSIDE"
