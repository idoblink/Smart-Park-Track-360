"""
ParkTrack 360 — tests/test_protocol.py
Unit tests verifying the FastAPI endpoints, UI snapshot schema, and checkout billing routes.
"""

import pytest
from fastapi.testclient import TestClient
from server.app import app, state

client = TestClient(app)

def test_api_snapshot():
    response = client.get("/api/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert data["t"] == "snapshot"
    assert "counts" in data
    assert data["counts"]["total"] == 8
    assert "slots" in data
    assert len(data["slots"]) == 8
    assert "cars" in data
    assert len(data["cars"]) == 8

def test_api_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "entries_today" in data
    assert "exits_today" in data
    assert "epoch_ts" in data

def test_entry_and_checkout_flow():
    # Make sure controller is considered online for test and car 1 is outside
    state.esp32_online = True
    state.esp32_calibrated = True
    state.cars[1]["state"] = "OUTSIDE"
    state.cars[1]["slot"] = None
    state.cars[1]["entered_ts"] = None
    state.cars[1]["visit_id"] = None
    state.slots["G1"]["occupied"] = False
    state.slots["G1"]["car"] = None

    # 1. Simulate car 1 entry
    resp = client.post("/api/entry", json={"car": 1})
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["ok"] is True

    # 2. Simulate car 1 occupying slot G1
    state._handle_slot_transition("G1", is_occupied=True)

    # 3. Process checkout & exit
    checkout_resp = client.post("/api/billing/checkout", json={"car": 1, "method": "UPI"})
    assert checkout_resp.status_code == 200
    c_data = checkout_resp.json()
    assert c_data["ok"] is True
    assert "receipt_id" in c_data
    assert c_data["car"] == 1

def test_pages_served():
    for path in ["/", "/payment", "/admin/login", "/admin"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "text/html" in res.headers.get("content-type", "")

def test_api_vehicle_lookup():
    res = client.get("/api/vehicle/2")
    assert res.status_code == 200
    data = res.json()
    assert data["car"] == 2
    assert "state" in data
    assert "dwell_s" in data
    assert "current_fare" in data

def test_admin_auth():
    # Valid credentials
    res_ok = client.post("/api/admin/login", json={"username": "admin", "password": "admin360"})
    assert res_ok.status_code == 200
    assert res_ok.json()["ok"] is True
    assert "token" in res_ok.json()

    # Invalid credentials
    res_bad = client.post("/api/admin/login", json={"username": "admin", "password": "wrongpassword"})
    assert res_bad.status_code == 401
    assert res_bad.json()["ok"] is False
