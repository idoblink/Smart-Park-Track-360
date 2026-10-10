"""
ParkTrack 360 — server/app.py
FastAPI backend server providing WebSocket endpoints for ESP32 controller and Browser Dashboard,
REST APIs for metrics/controls, and billing checkout workflows.
"""

import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Dict, Set, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from server.state import ParkingState
from server import db
from server.serial_comm import ESP32SerialManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("parktrack")

state = ParkingState()

# WebSocket client sets
esp32_socket: Optional[WebSocket] = None
ui_sockets: Set[WebSocket] = set()

main_loop: Optional[asyncio.AbstractEventLoop] = None
serial_mgr: Optional[ESP32SerialManager] = None

# Helper to dispatch ESP32 message from either Serial or WebSocket
def process_esp32_message(data: Dict[str, Any]):
    global main_loop
    t = data.get("t")
    if t == "hello":
        state.handle_esp32_hello(
            fw=data.get("fw", "1.1.0"),
            ip=data.get("ip", "usb_serial"),
            calibrated=data.get("calibrated", False),
            reset_reason=data.get("reset_reason", "power_on")
        )
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_ui_snapshot(), main_loop)

    elif t == "state":
        state.handle_esp32_state(
            slots_data=data.get("slots", []),
            dist_data=data.get("dist", []),
            fault_data=data.get("fault", []),
            entry_gate=data.get("entry", "closed"),
            exit_gate=data.get("exit", "closed"),
            calibrated=data.get("calibrated", False),
            free_count=data.get("free", 8),
            uptime=data.get("uptime", 0)
        )
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_ui_snapshot(), main_loop)

    elif t == "gate_result":
        gate = data.get("gate")
        ok = data.get("ok", False)
        reason = data.get("reason", "unknown")
        req_id = data.get("req_id", "")
        logger.info(f"Gate result: {gate} ok={ok} reason={reason} req_id={req_id}")
        
        if gate == "entry" and not ok and req_id.startswith("car_"):
            try:
                car_id = int(req_id.split("_")[1])
                state.rollback_entry(car_id, reason)
                if main_loop and main_loop.is_running():
                    asyncio.run_coroutine_threadsafe(broadcast_ui_snapshot(), main_loop)
            except Exception as e:
                logger.error(f"Rollback parsing error: {e}")

    elif t == "cal_result":
        ok = data.get("ok", False)
        state.esp32_calibrated = ok
        db.log_event("calibrate", detail="success" if ok else "failed")
        if main_loop and main_loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_ui_snapshot(), main_loop)

    elif t == "cal_progress":
        pass

def on_serial_status_change(connected: bool):
    global main_loop
    state.esp32_online = connected
    if connected:
        state.last_esp32_msg_ts = time.time()
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_ui_snapshot(), main_loop)

# Helper to send message to ESP32 (via USB Serial and/or WebSocket)
async def send_to_esp32(payload: Dict[str, Any]) -> bool:
    global esp32_socket, serial_mgr
    sent_serial = False
    if serial_mgr and serial_mgr.connected:
        sent_serial = serial_mgr.send(payload)

    sent_ws = False
    if esp32_socket:
        try:
            await esp32_socket.send_text(json.dumps(payload))
            sent_ws = True
        except Exception as e:
            logger.error(f"Failed to send to ESP32 socket: {e}")
            esp32_socket = None

    return sent_serial or sent_ws

# Broadcast state snapshot to all connected UI browser clients
async def broadcast_ui_snapshot():
    if not ui_sockets:
        return
    snapshot = state.get_snapshot()
    msg = json.dumps(snapshot)
    disconnected = set()
    for ws in ui_sockets:
        try:
            await ws.send_text(msg)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        ui_sockets.discard(ws)

# Periodic background task to check ESP32 heartbeat and link status
async def background_heartbeat_loop():
    while True:
        try:
            await asyncio.sleep(1.0)
            was_online = state.esp32_online
            state.check_link_liveness()
            if was_online != state.esp32_online:
                await broadcast_ui_snapshot()
            
            # Send server heartbeat to ESP32
            await send_to_esp32({"t": "hb"})
        except Exception as e:
            logger.error(f"Error in background heartbeat loop: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop, serial_mgr
    main_loop = asyncio.get_running_loop()

    # Start USB Serial worker for direct cable connection
    port = state.config.get("esp32", {}).get("port", "auto")
    baud = state.config.get("esp32", {}).get("baud", 115200)
    serial_mgr = ESP32SerialManager(
        port=port, baudrate=baud,
        on_json=process_esp32_message,
        on_status_change=on_serial_status_change
    )
    serial_mgr.start()

    hb_task = asyncio.create_task(background_heartbeat_loop())
    yield
    hb_task.cancel()
    if serial_mgr:
        serial_mgr.stop()

app = FastAPI(title="ParkTrack 360 API", version="1.1.0", lifespan=lifespan)

# --- WebSocket: ESP32 Controller (/ws/esp32) ---

@app.websocket("/ws/esp32")
async def websocket_esp32_endpoint(websocket: WebSocket):
    global esp32_socket
    if esp32_socket and esp32_socket != websocket:
        try:
            await esp32_socket.close()
        except Exception:
            pass
    await websocket.accept()
    esp32_socket = websocket
    state.esp32_online = True
    state.last_esp32_msg_ts = time.time()
    logger.info("ESP32 controller connected via WebSocket")

    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
            except Exception:
                logger.warning(f"Invalid JSON from ESP32: {text}")
                continue

            process_esp32_message(data)

    except WebSocketDisconnect:
        logger.info("ESP32 disconnected")
    except Exception as e:
        logger.error(f"ESP32 socket exception: {e}")
    finally:
        if esp32_socket == websocket:
            esp32_socket = None
        state.esp32_online = False
        await broadcast_ui_snapshot()

# --- WebSocket: UI Browser Dashboard (/ws/ui) ---

@app.websocket("/ws/ui")
async def websocket_ui_endpoint(websocket: WebSocket):
    await websocket.accept()
    ui_sockets.add(websocket)
    logger.info(f"UI browser connected ({len(ui_sockets)} active)")

    # Immediately deliver snapshot
    try:
        await websocket.send_text(json.dumps(state.get_snapshot()))
    except Exception:
        ui_sockets.discard(websocket)
        return

    try:
        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            t = data.get("t")

            if t == "gate":
                gate = data.get("gate")
                action = data.get("action", "open")
                hold_ms = data.get("hold_ms", state.config.get("gate", {}).get("hold_ms", 5000))
                req_id = f"manual_{gate}_{int(time.time())}"
                
                # Forward to ESP32
                await send_to_esp32({
                    "t": "gate",
                    "gate": gate,
                    "action": action,
                    "hold_ms": hold_ms,
                    "req_id": req_id
                })
                db.log_event("manual_gate", detail=f"{gate} {action}")
                # Optimistically update local gate state
                state.gates[gate] = "opening" if action == "open" else "closing"
                await broadcast_ui_snapshot()

            elif t == "cmd":
                cmd = data.get("cmd")
                if cmd == "calibrate":
                    await send_to_esp32({"t": "cmd", "cmd": "calibrate"})
                    db.log_event("calibrate", detail="requested_by_ui")
                elif cmd == "reset_counters":
                    db.reset_stats()
                    state.peak_today = state.get_occupied_count()
                    db.log_event("stats_reset", detail="counters reset by user")
                    await broadcast_ui_snapshot()

            elif t == "assign":
                slot = data.get("slot")
                car = data.get("car")
                state.manual_assign_slot(slot, car)
                await broadcast_ui_snapshot()

    except WebSocketDisconnect:
        ui_sockets.discard(websocket)
    except Exception as e:
        logger.error(f"UI socket exception: {e}")
        ui_sockets.discard(websocket)

# --- REST API Endpoints ---

@app.get("/api/snapshot")
async def get_snapshot_endpoint():
    return JSONResponse(state.get_snapshot())

@app.get("/api/stats")
async def get_stats_endpoint():
    return JSONResponse(db.get_stats())

class GateRequest(BaseModel):
    gate: str
    action: str = "open"
    hold_ms: Optional[int] = 5000

@app.post("/api/gate")
async def post_gate_endpoint(req: GateRequest):
    if req.gate not in ["entry", "exit"] or req.action not in ["open", "close"]:
        raise HTTPException(status_code=400, detail="Invalid gate or action")
    
    req_id = f"manual_{req.gate}_{int(time.time())}"
    sent = await send_to_esp32({
        "t": "gate",
        "gate": req.gate,
        "action": req.action,
        "hold_ms": req.hold_ms,
        "req_id": req_id
    })
    db.log_event("manual_gate", detail=f"{req.gate} {req.action}")
    state.gates[req.gate] = "opening" if req.action == "open" else "closing"
    await broadcast_ui_snapshot()
    return {"ok": True, "sent_to_esp32": sent}

class EntryRequest(BaseModel):
    car: int

@app.post("/api/entry")
async def post_entry_endpoint(req: EntryRequest):
    ok, reason = state.authorize_entry(req.car)
    if not ok:
        db.log_event("deny", car=req.car, detail=f"entry_denied: {reason}")
        await broadcast_ui_snapshot()
        return {"ok": False, "reason": reason}

    # Dispatch gate open command to ESP32
    req_id = f"car_{req.car}_{int(time.time())}"
    sent = await send_to_esp32({
        "t": "gate",
        "gate": "entry",
        "action": "open",
        "hold_ms": state.config.get("gate", {}).get("hold_ms", 5000),
        "req_id": req_id
    })
    state.gates["entry"] = "opening"
    await broadcast_ui_snapshot()
    return {"ok": True, "message": f"Car {req.car} approved for entry", "sent_to_esp32": sent}

class CheckoutRequest(BaseModel):
    car: int
    method: str = "UPI"

@app.post("/api/billing/checkout")
async def post_checkout_endpoint(req: CheckoutRequest):
    """Processes payment settlement and opens exit gate."""
    ok, reason, fare = state.authorize_exit(req.car)
    if not ok:
        return {"ok": False, "reason": reason}

    # Send gate open to ESP32
    req_id = f"exit_car_{req.car}_{int(time.time())}"
    sent = await send_to_esp32({
        "t": "gate",
        "gate": "exit",
        "action": "open",
        "hold_ms": state.config.get("gate", {}).get("hold_ms", 5000),
        "req_id": req_id
    })
    state.gates["exit"] = "opening"
    await broadcast_ui_snapshot()

    return {
        "ok": True,
        "car": req.car,
        "fare": fare,
        "currency": state.currency,
        "payment_method": req.method,
        "receipt_id": f"RCP-{req.car}-{int(time.time())}",
        "message": f"Payment of {fare} {state.currency} completed. Exit gate open.",
        "sent_to_esp32": sent
    }

class AssignRequest(BaseModel):
    slot: str
    car: Optional[int] = None

@app.post("/api/assign")
async def post_assign_endpoint(req: AssignRequest):
    ok = state.manual_assign_slot(req.slot, req.car)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid slot")
    await broadcast_ui_snapshot()
    return {"ok": True}

@app.get("/api/vehicle/{car_id}")
async def get_vehicle_status(car_id: int):
    if car_id < 1 or car_id > 8:
        raise HTTPException(status_code=400, detail="Invalid car ID (must be 1-8)")
    car = state.cars.get(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    dwell_s, fare = state.compute_fare(car.get("entered_ts"))
    return {
        "car": car_id,
        "state": car["state"],
        "slot": car["slot"],
        "entered_ts": car["entered_ts"],
        "dwell_s": round(dwell_s, 0) if car["state"] != "OUTSIDE" else 0,
        "current_fare": fare if car["state"] != "OUTSIDE" else 0.0,
        "currency": state.currency,
        "first_hour_fee": state.first_hour_fee,
        "additional_hourly_rate": state.additional_hourly_rate,
        "base_fee": state.base_fee,
        "hourly_rate": state.hourly_rate,
        "grace_period_min": state.grace_period_min
    }

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/admin/login")
async def post_admin_login(req: AdminLoginRequest):
    if req.username == "admin" and req.password == "admin360":
        return {"ok": True, "token": "pts360_adm_session_token", "message": "Authentication successful"}
    return JSONResponse(status_code=401, content={"ok": False, "detail": "Invalid administrator credentials"})

# Serve static UI files & Dedicated Pages
STATIC_DIR = Path("server/static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"status": "Server running", "ui": "static/index.html not found"})

@app.get("/payment")
async def serve_payment():
    p_file = STATIC_DIR / "payment.html"
    if p_file.exists():
        return FileResponse(p_file)
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/admin/login")
async def serve_admin_login():
    l_file = STATIC_DIR / "admin_login.html"
    if l_file.exists():
        return FileResponse(l_file)
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/admin")
async def serve_admin():
    a_file = STATIC_DIR / "admin.html"
    if a_file.exists():
        return FileResponse(a_file)
    return FileResponse(STATIC_DIR / "index.html")
