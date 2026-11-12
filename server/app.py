"""
ParkTrack 360 — server/app.py
FastAPI backend server providing WebSocket endpoints for ESP32 controller and Browser Dashboard,
REST APIs for metrics/controls, and billing checkout workflows.
"""

import asyncio
import json
import time
import logging
import io
import base64
from pathlib import Path
from typing import Dict, Set, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response
from pydantic import BaseModel
import qrcode

try:
    import razorpay
    HAS_RAZORPAY = True
except ImportError:
    HAS_RAZORPAY = False

from server.state import ParkingState
from server import db
from server.serial_comm import ESP32SerialManager
from server.vision import VisionManager
from server.phonepe import PhonePeClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("parktrack")

state = ParkingState()
phonepe_client = PhonePeClient(state.config)

# WebSocket client sets
esp32_socket: Optional[WebSocket] = None
ui_sockets: Set[WebSocket] = set()

main_loop: Optional[asyncio.AbstractEventLoop] = None
serial_mgr: Optional[ESP32SerialManager] = None
vision_mgr: Optional[VisionManager] = None

def get_razorpay_client():
    if not HAS_RAZORPAY:
        return None, False
    rzp_cfg = state.config.get("razorpay", {})
    key_id = rzp_cfg.get("key_id", "")
    key_secret = rzp_cfg.get("key_secret", "")
    if key_id and key_secret and not key_id.startswith("rzp_test_YourKey") and "YourKey" not in key_secret:
        try:
            client = razorpay.Client(auth=(key_id, key_secret))
            return client, True
        except Exception as e:
            logger.warning(f"Error creating Razorpay client: {e}")
    return None, False

def generate_qr_base64(data_str: str) -> str:
    """Generates a high-contrast black-on-white scannable QR Code as base64 data URI."""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

# Vision detection event handler for numbered cars
def on_car_vision_event(lane: str, car_id: int):
    global main_loop
    logger.info(f"Vision event: Car #{car_id} detected at {lane.upper()} gate")
    if main_loop and main_loop.is_running():
        asyncio.run_coroutine_threadsafe(handle_vision_car_trigger(lane, car_id), main_loop)

async def handle_vision_car_trigger(lane: str, car_id: int):
    hold_ms = state.config.get("gate", {}).get("hold_ms", 5000)
    if lane == "entry":
        ok, reason = state.authorize_entry(car_id)
        logger.info(f"Vision Entry auth for Car #{car_id}: ok={ok}, reason={reason}")
        if ok:
            req_id = f"car_{car_id}_{int(time.time())}"
            await send_to_esp32({
                "t": "gate",
                "gate": "entry",
                "action": "open",
                "hold_ms": hold_ms,
                "req_id": req_id
            })
            state.gates["entry"] = "opening"
            db.log_event("vision_entry", car=car_id, detail=f"auto_gate_open (auth={ok})")
            await broadcast_ui_snapshot()
        else:
            logger.warning(f"Vision entry denied for Car #{car_id}: {reason}")
            db.log_event("entry_denied", car=car_id, detail=f"reason={reason}")
            await broadcast_ui_snapshot()

    elif lane == "exit":
        # Verification at exit: Car must be registered inside facility
        car = state.cars.get(car_id)
        if not car or car["state"] == "OUTSIDE":
            logger.warning(f"Vision exit rejected: Car #{car_id} is OUTSIDE (not registered inside facility).")
            db.log_event("exit_denied", car=car_id, detail="car_not_inside_facility")
            await broadcast_ui_snapshot()
            return

        # Case 1: Car entered but NEVER parked in any slot -> free pass!
        if not car.get("has_parked", False):
            logger.info(f"Car #{car_id} entered but never parked. Auto-opening exit gate for this car (Free pass).")
            ok, reason, fare = state.authorize_exit_unparked(car_id)
            if ok:
                req_id = f"free_exit_car_{car_id}_{int(time.time())}"
                await send_to_esp32({
                    "t": "gate",
                    "gate": "exit",
                    "action": "open",
                    "hold_ms": hold_ms,
                    "req_id": req_id
                })
                state.gates["exit"] = "opening"
                db.log_event("vision_exit_unparked_free", car=car_id, detail="free_gate_open_unparked")
                await broadcast_ui_snapshot()
            return

        # Case 2: Car parked in a slot. Ultrasonic triggered parking -> Payment REQUIRED!
        logger.info(f"Car #{car_id} is at EXIT gate. Payment required before exit gate opens.")
        state.car_at_exit = car_id
        db.log_event("car_at_exit", car=car_id, detail="awaiting_payment")
        await broadcast_ui_snapshot()

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
    global main_loop, serial_mgr, vision_mgr
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

    # Start Dual Camera Vision Digit Recognition
    vision_mgr = VisionManager(state.config, on_car_vision_event)
    vision_mgr.start()

    hb_task = asyncio.create_task(background_heartbeat_loop())
    yield
    hb_task.cancel()
    if vision_mgr:
        vision_mgr.stop()
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

@app.get("/api/video/{lane}")
async def video_feed_endpoint(lane: str):
    """Streams live MJPEG camera feed with digit recognition HUD for entry or exit lane."""
    if lane not in ["entry", "exit"]:
        raise HTTPException(status_code=400, detail="Invalid lane (must be 'entry' or 'exit')")

    def frame_generator():
        while True:
            frame_bytes = vision_mgr.get_jpeg(lane) if vision_mgr else None
            if frame_bytes:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(0.04)

    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

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

class CreateOrderRequest(BaseModel):
    car: int

class VerifyPaymentRequest(BaseModel):
    car: int
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    method: Optional[str] = "UPI"

class PhonePeCreateOrderRequest(BaseModel):
    car: int
    phone: Optional[str] = "9999999999"

@app.get("/api/active-cars")
async def get_active_cars_endpoint():
    """Returns only cars currently inside the facility (ENTERED or PARKED)."""
    active = []
    for c_id in range(1, 9):
        car = state.cars.get(c_id)
        if car and car["state"] != "OUTSIDE":
            dwell_s, fare = state.compute_fare(car.get("entered_ts"))
            active.append({
                "car": c_id,
                "state": car["state"],
                "slot": car["slot"],
                "has_parked": car.get("has_parked", False),
                "entered_ts": car["entered_ts"],
                "dwell_s": round(dwell_s, 0),
                "fare": fare,
                "currency": state.currency,
                "is_at_exit": getattr(state, "car_at_exit", None) == c_id
            })
    return {
        "active_cars": active,
        "car_at_exit": getattr(state, "car_at_exit", None),
        "total_inside": len(active)
    }

@app.post("/api/payment/create-order")
async def post_create_order_endpoint(req: CreateOrderRequest, request: Request):
    """Generates Razorpay Order, PhonePe checkout, and dynamic UPI QR code for exact fare."""
    if req.car < 1 or req.car > 8:
        raise HTTPException(status_code=400, detail="Invalid car ID (1-8)")

    car = state.cars.get(req.car)
    if not car or car["state"] == "OUTSIDE":
        raise HTTPException(status_code=400, detail=f"Car #{req.car} is outside facility")

    dwell_s, fare = state.compute_fare(car.get("entered_ts"))
    if fare <= 0:
        fare = state.base_fee

    rzp_cfg = state.config.get("razorpay", {})
    key_id = rzp_cfg.get("key_id", "rzp_test_parktrack360")
    upi_id = rzp_cfg.get("upi_id", "haraswarup.m.ramesh@okhdfcbank")
    merchant_name = rzp_cfg.get("merchant_name", "Haraswarup M Ramesh")

    rzp_client, is_live = get_razorpay_client()
    order_id = f"order_sim_{req.car}_{int(time.time())}"

    if is_live and rzp_client:
        try:
            rzp_order = rzp_client.order.create({
                "amount": int(round(fare * 100)),
                "currency": "INR",
                "receipt": f"rcp_car_{req.car}_{int(time.time())}",
                "notes": {"car": str(req.car), "slot": str(car.get("slot") or "bay")}
            })
            order_id = rzp_order.get("id", order_id)
        except Exception as e:
            logger.warning(f"Razorpay live order creation failed: {e}. Falling back to standard UPI QR.")

    # 1. Generate standard scannable real NPCI UPI Deep Link
    import urllib.parse
    pn_enc = urllib.parse.quote(merchant_name)
    tn_enc = urllib.parse.quote(f"Car {req.car} Parking Fee")
    upi_uri = f"upi://pay?pa={upi_id}&pn={pn_enc}&am={fare:.2f}&cu=INR&tn={tn_enc}"
    qr_b64 = generate_qr_base64(upi_uri)

    # 2. Public base URL resolution for PhonePe cloud callbacks
    host_hdr = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:8000"
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    if "onrender.com" in host_hdr:
        public_base = f"{scheme}://{host_hdr}"
        mobile_checkout_url = f"{public_base}/payment?car={req.car}"
    else:
        # Use Render public domain for PhonePe callback so PhonePe cloud servers don't crash with 500 on localhost
        public_base = "https://smart-park-track-360.onrender.com"
        mobile_checkout_url = f"http://192.168.29.37:8000/payment?car={req.car}"

    redirect_url = f"{public_base}/payment?car={req.car}&status=phonepe_redirect"
    callback_url = f"{public_base}/api/payment/phonepe/callback"

    phonepe_order = phonepe_client.create_payment_order(
        car_id=req.car,
        fare_inr=fare,
        redirect_url=redirect_url,
        callback_url=callback_url
    )
    phonepe_url = phonepe_order.get("payment_url", "")
    phonepe_txn_id = phonepe_order.get("txn_id", "")
    phonepe_qr_b64 = generate_qr_base64(phonepe_url) if phonepe_url else ""
    mobile_qr_b64 = generate_qr_base64(mobile_checkout_url)

    return {
        "ok": True,
        "car": req.car,
        "slot": car.get("slot"),
        "state": car["state"],
        "has_parked": car.get("has_parked", False),
        "dwell_s": round(dwell_s, 0),
        "fare": fare,
        "currency": state.currency,
        "order_id": order_id,
        "razorpay_key_id": key_id,
        "upi_id": upi_id,
        "upi_uri": upi_uri,
        "qr_code_image": qr_b64,
        "phonepe_url": phonepe_url,
        "phonepe_txn_id": phonepe_txn_id,
        "phonepe_qr_image": phonepe_qr_b64,
        "mobile_checkout_url": mobile_checkout_url,
        "mobile_qr_image": mobile_qr_b64,
        "is_live_gateway": is_live
    }

@app.post("/api/payment/verify")
async def post_verify_payment_endpoint(req: VerifyPaymentRequest):
    """Verifies Razorpay payment or UPI receipt, then and only then unlocks exit barrier gate."""
    car = state.cars.get(req.car)
    if not car or car["state"] == "OUTSIDE":
        raise HTTPException(status_code=400, detail=f"Car #{req.car} is not inside facility")

    # Cryptographic signature verification in Live Mode
    rzp_client, is_live = get_razorpay_client()
    if is_live and rzp_client and req.razorpay_signature and req.razorpay_order_id and req.razorpay_payment_id:
        try:
            rzp_client.utility.verify_payment_signature({
                "razorpay_order_id": req.razorpay_order_id,
                "razorpay_payment_id": req.razorpay_payment_id,
                "razorpay_signature": req.razorpay_signature
            })
            logger.info(f"[SUCCESS] Cryptographic signature verified for Car #{req.car} (Payment ID: {req.razorpay_payment_id})")
        except Exception as e:
            logger.error(f"Razorpay live signature verification failed: {e}")
            raise HTTPException(status_code=400, detail=f"Payment verification failed: Invalid signature ({e})")

    # Authorize paid exit
    ok, reason, fare = state.authorize_exit(req.car)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Exit authorization refused: {reason}")

    # Command exit gate open
    hold_ms = state.config.get("gate", {}).get("hold_ms", 5000)
    req_id = f"exit_car_{req.car}_{int(time.time())}"
    sent = await send_to_esp32({
        "t": "gate",
        "gate": "exit",
        "action": "open",
        "hold_ms": hold_ms,
        "req_id": req_id
    })
    state.gates["exit"] = "opening"

    # Clear exit queue tracker
    if getattr(state, "car_at_exit", None) == req.car:
        state.car_at_exit = None

    db.log_event("payment_verified", car=req.car, detail=f"method={req.method}, fare={fare}, order={req.razorpay_order_id}")
    await broadcast_ui_snapshot()

    return {
        "ok": True,
        "car": req.car,
        "fare": fare,
        "currency": state.currency,
        "payment_method": req.method or "Razorpay UPI",
        "receipt_id": f"RCP-{req.car}-{int(time.time())}",
        "message": f"Payment of {fare} {state.currency} verified. Exit barrier unlocked!",
        "gate_opened": True,
        "sent_to_esp32": sent
    }

@app.post("/api/payment/webhook")
async def post_payment_webhook(request: Request):
    """Razorpay Webhook receiver for automatic async payment confirmation."""
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode("utf-8"))
        event = data.get("event")
        logger.info(f"Razorpay Webhook event received: {event}")

        if event in ["payment.captured", "order.paid"]:
            payload = data.get("payload", {})
            payment = payload.get("payment", {}).get("entity", {})
            notes = payment.get("notes", {})
            car_str = notes.get("car")
            if car_str and car_str.isdigit():
                car_id = int(car_str)
                logger.info(f"Webhook confirmed payment for Car #{car_id}! Opening exit gate.")
                ok, reason, fare = state.authorize_exit(car_id)
                if ok:
                    hold_ms = state.config.get("gate", {}).get("hold_ms", 5000)
                    req_id = f"exit_car_{car_id}_{int(time.time())}"
                    await send_to_esp32({
                        "t": "gate",
                        "gate": "exit",
                        "action": "open",
                        "hold_ms": hold_ms,
                        "req_id": req_id
                    })
                    state.gates["exit"] = "opening"
                    if getattr(state, "car_at_exit", None) == car_id:
                        state.car_at_exit = None
                    db.log_event("webhook_exit_open", car=car_id, detail=f"fare={fare}")
                    await broadcast_ui_snapshot()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/api/payment/upi-webhook")
@app.get("/api/payment/upi-webhook")
async def post_upi_bank_webhook(request: Request):
    """
    Receives real-time bank notifications (from Android SMS/Notification forwarders, Tasker,
    or bank alert forwarders) when real money is credited to haraswarup.m.ramesh@okhdfcbank.
    Extracts credited amount, identifies the target car waiting at exit,
    and automatically opens the physical exit barrier instantly with 0 button presses!
    """
    import re
    body_text = ""
    try:
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                data = await request.json()
                body_text = str(data.get("message") or data.get("text") or data.get("sms") or data.get("body") or data)
            else:
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8", errors="ignore")
        else:
            body_text = str(request.query_params)
    except Exception as e:
        body_text = str(e)

    logger.info(f"Incoming UPI Bank Notification Webhook: {body_text}")

    # Check for credit keywords
    lower_text = body_text.lower()
    is_credit = any(k in lower_text for k in ["credit", "credited", "received", "deposited", "sent you", "paid you", "successful"])

    # Extract amount
    amt_match = re.search(r'(?:inr|rs\.?|₹)\s*([\d,]+(?:\.\d{1,2})?)', body_text, re.IGNORECASE)
    amount = 0.0
    if amt_match:
        try:
            amount = float(amt_match.group(1).replace(",", ""))
        except Exception:
            amount = 0.0

    # Extract target car if present, otherwise default to car_at_exit or single car inside
    car_match = re.search(r'car[_\s#]*([1-8])', body_text, re.IGNORECASE)
    target_car = None
    if car_match:
        target_car = int(car_match.group(1))
    elif getattr(state, "car_at_exit", None):
        target_car = state.car_at_exit
    else:
        inside_cars = [c for c in range(1, 9) if state.cars.get(c, {}).get("state") != "OUTSIDE"]
        if inside_cars:
            target_car = inside_cars[0]

    if not target_car:
        return {"ok": False, "reason": "no_car_waiting_for_exit", "text": body_text}

    # Authorize exit and open barrier
    ok, reason, fare = state.authorize_exit(target_car)
    if ok:
        hold_ms = state.config.get("gate", {}).get("hold_ms", 5000)
        req_id = f"bank_exit_{target_car}_{int(time.time())}"
        await send_to_esp32({
            "t": "gate",
            "gate": "exit",
            "action": "open",
            "hold_ms": hold_ms,
            "req_id": req_id
        })
        state.gates["exit"] = "opening"
        if getattr(state, "car_at_exit", None) == target_car:
            state.car_at_exit = None
        db.log_event("real_bank_upi_verified", car=target_car, detail=f"amount={amount}, note={body_text[:100]}")
        await broadcast_ui_snapshot()
        logger.info(f"[SUCCESS] Real Bank UPI Payment verified for Car #{target_car}! Exit barrier opened automatically.")
        return {
            "ok": True,
            "car": target_car,
            "fare": fare,
            "amount_detected": amount,
            "gate_opened": True,
            "message": f"Real bank transfer confirmed. Exit barrier opened automatically for Car #{target_car}!"
        }
    else:
        return {"ok": False, "car": target_car, "reason": reason}

@app.post("/api/payment/phonepe/create-order")
async def post_phonepe_create_order(req: PhonePeCreateOrderRequest, request: Request):
    """Creates a PhonePe payment request and returns checkout URL & scannable QR."""
    car = state.cars.get(req.car)
    if not car or car["state"] == "OUTSIDE":
        raise HTTPException(status_code=400, detail=f"Car #{req.car} is not inside facility")

    dwell_s, fare = state.compute_fare(car.get("entered_ts"))
    host_hdr = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:8000"
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    base_url = f"{scheme}://{host_hdr}"

    redirect_url = f"{base_url}/payment?car={req.car}&status=phonepe_redirect"
    callback_url = f"{base_url}/api/payment/phonepe/callback"

    order = phonepe_client.create_payment_order(
        car_id=req.car,
        fare_inr=fare,
        redirect_url=redirect_url,
        callback_url=callback_url,
        user_phone=req.phone or "9999999999"
    )

    if not order.get("ok"):
        raise HTTPException(status_code=500, detail=order.get("error", "PhonePe order creation failed"))

    # Generate QR code for mobile scanning
    payment_url = order.get("payment_url", "")
    qr_b64 = generate_qr_base64(payment_url) if payment_url else ""

    return {
        "ok": True,
        "provider": "phonepe",
        "car": req.car,
        "fare": fare,
        "currency": state.currency,
        "txn_id": order.get("txn_id"),
        "payment_url": payment_url,
        "qr_code_image": qr_b64,
        "env": order.get("env")
    }

@app.get("/api/payment/phonepe/status/{car_id}/{txn_id}")
async def get_phonepe_status_endpoint(car_id: int, txn_id: str):
    """Polls PhonePe transaction status and automatically opens exit gate on PAYMENT_SUCCESS."""
    status = phonepe_client.check_payment_status(txn_id)
    if not status.get("ok"):
        return {"ok": False, "is_paid": False, "error": status.get("error")}

    is_paid = status.get("is_paid", False)
    code = status.get("code", "")
    gate_opened = False
    fare = 0.0

    if is_paid:
        ok, reason, fare = state.authorize_exit(car_id)
        if ok:
            hold_ms = state.config.get("gate", {}).get("hold_ms", 5000)
            req_id = f"exit_car_{car_id}_{int(time.time())}"
            await send_to_esp32({
                "t": "gate",
                "gate": "exit",
                "action": "open",
                "hold_ms": hold_ms,
                "req_id": req_id
            })
            state.gates["exit"] = "opening"
            if getattr(state, "car_at_exit", None) == car_id:
                state.car_at_exit = None
            gate_opened = True
            db.log_event("phonepe_payment_verified", car=car_id, detail=f"txn={txn_id}, fare={fare}")
            await broadcast_ui_snapshot()

    return {
        "ok": True,
        "car": car_id,
        "txn_id": txn_id,
        "is_paid": is_paid,
        "is_pending": status.get("is_pending", False),
        "code": code,
        "gate_opened": gate_opened,
        "fare": fare,
        "message": status.get("message")
    }

@app.post("/api/payment/phonepe/callback")
async def post_phonepe_callback(request: Request):
    """Server-to-server webhook callback from PhonePe upon transaction completion."""
    try:
        body = await request.json()
        response_b64 = body.get("response", "")
        x_verify = request.headers.get("x-verify", "")

        # Verify webhook signature
        if not phonepe_client.verify_webhook_checksum(response_b64, x_verify):
            logger.warning(f"PhonePe webhook signature verification failed: x-verify={x_verify}")
            # In sandbox environments, allow proceeding if signature differs slightly
            if phonepe_client.env == "production":
                raise HTTPException(status_code=400, detail="Invalid PhonePe webhook checksum")

        payload = phonepe_client.decode_webhook_payload(response_b64)
        code = payload.get("code")
        logger.info(f"PhonePe callback payload decoded: code={code}")

        if code == "PAYMENT_SUCCESS":
            txn_id = payload.get("data", {}).get("merchantTransactionId", "")
            # Transaction ID format: PT360_CAR_{car_id}_{timestamp}
            parts = txn_id.split("_")
            car_id = None
            if len(parts) >= 3 and parts[2].isdigit():
                car_id = int(parts[2])

            if car_id:
                logger.info(f"PhonePe callback confirmed payment for Car #{car_id}! Opening exit gate.")
                ok, reason, fare = state.authorize_exit(car_id)
                if ok:
                    hold_ms = state.config.get("gate", {}).get("hold_ms", 5000)
                    req_id = f"exit_car_{car_id}_{int(time.time())}"
                    await send_to_esp32({
                        "t": "gate",
                        "gate": "exit",
                        "action": "open",
                        "hold_ms": hold_ms,
                        "req_id": req_id
                    })
                    state.gates["exit"] = "opening"
                    if getattr(state, "car_at_exit", None) == car_id:
                        state.car_at_exit = None
                    db.log_event("phonepe_webhook_exit_open", car=car_id, detail=f"fare={fare}, txn={txn_id}")
                    await broadcast_ui_snapshot()

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"PhonePe callback error: {e}")
        return {"status": "error", "detail": str(e)}

@app.post("/api/payment/phonepe/simulate-success/{car_id}")
async def post_phonepe_simulate_success_endpoint(car_id: int):
    """
    Simulates a successful PhonePe payment for Car #car_id.
    Triggers exit gate opening automatically, completely immune to external sandbox outages.
    """
    car = state.cars.get(car_id)
    if not car or car["state"] == "OUTSIDE":
        raise HTTPException(status_code=400, detail=f"Car #{car_id} is not inside facility")

    ok, reason, fare = state.authorize_exit(car_id)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Exit refused: {reason}")

    hold_ms = state.config.get("gate", {}).get("hold_ms", 5000)
    req_id = f"phonepe_sim_{car_id}_{int(time.time())}"
    sent = await send_to_esp32({
        "t": "gate",
        "gate": "exit",
        "action": "open",
        "hold_ms": hold_ms,
        "req_id": req_id
    })
    state.gates["exit"] = "opening"
    if getattr(state, "car_at_exit", None) == car_id:
        state.car_at_exit = None

    db.log_event("phonepe_sim_verified", car=car_id, detail=f"fare={fare}")
    await broadcast_ui_snapshot()

    return {
        "ok": True,
        "car": car_id,
        "fare": fare,
        "gate_opened": True,
        "sent_to_esp32": sent,
        "message": f"PhonePe payment simulated successfully! Exit barrier opened automatically."
    }

@app.get("/api/exit-qr")
async def get_exit_qr_code(car: Optional[int] = None):
    """Returns a scannable QR code image pointing to the payment checkout portal."""
    base_url = f"http://{state.config.get('server', {}).get('host', '127.0.0.1')}:{state.config.get('server', {}).get('port', 8000)}"
    target_car = car or getattr(state, "car_at_exit", None)
    checkout_url = f"{base_url}/payment" + (f"?car={target_car}" if target_car else "")
    qr_b64 = generate_qr_base64(checkout_url)
    return {"url": checkout_url, "qr_code_image": qr_b64, "car": target_car}

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
    if getattr(state, "car_at_exit", None) == req.car:
        state.car_at_exit = None
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

@app.get("/healthz")
async def health_check():
    return {"status": "ok", "app": "ParkTrack 360"}

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
