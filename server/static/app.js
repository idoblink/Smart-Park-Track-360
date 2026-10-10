/* =====================================================================
 *  ParkTrack 360 — app.js
 *  WebSocket client, dynamic slot rendering, live dwell timers,
 *  gate controllers, and QR code billing settlement.
 * =====================================================================*/

let ws = null;
let reconnectTimer = null;
let reconnectDelay = 1000;
let currentSnapshot = null;
let selectedSlotForAssign = null;
let pendingCheckoutCar = null;

// Clock
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const clockEl = document.getElementById('clockDisplay');
    if (clockEl) clockEl.textContent = timeStr;
}
setInterval(updateClock, 1000);
updateClock();

// Connect to WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/ui`;

    console.log(`[WS] Connecting to ${wsUrl}...`);
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[WS] Connected to server.');
        reconnectDelay = 1000;
        document.getElementById('reconnectBanner').classList.add('hidden');
    };

    ws.onmessage = (event) => {
        try {
            const data = jsonParse(event.data);
            if (data && data.t === 'snapshot') {
                renderSnapshot(data);
            }
        } catch (e) {
            console.error('[WS] Error processing message:', e);
        }
    };

    ws.onclose = () => {
        console.warn(`[WS] Disconnected. Reconnecting in ${reconnectDelay / 1000}s...`);
        document.getElementById('reconnectBanner').classList.remove('hidden');
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectWebSocket, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 1.5, 5000);
    };

    ws.onerror = (err) => {
        console.error('[WS] Socket error:', err);
        ws.close();
    };
}

function jsonParse(str) {
    try {
        return JSON.parse(str);
    } catch {
        return null;
    }
}

// Render Snapshot onto Dashboard
function renderSnapshot(data) {
    currentSnapshot = data;

    // 1. ESP32 Link Status
    const espBadge = document.getElementById('espStatusBadge');
    const espText = document.getElementById('espStatusText');
    if (data.esp32.online) {
        espBadge.className = 'status-pill online';
        espText.textContent = `ESP32: Online (${data.esp32.ip})`;
    } else {
        espBadge.className = 'status-pill offline';
        espText.textContent = 'ESP32: Offline';
    }

    // 2. Calibration Badge
    const calBadge = document.getElementById('calStatusBadge');
    const calText = document.getElementById('calStatusText');
    if (data.esp32.calibrated) {
        calBadge.className = 'status-pill calibrated';
        calText.textContent = 'Calibrated ✔';
    } else {
        calBadge.className = 'status-pill uncalibrated';
        calText.textContent = 'Uncalibrated ⚠️';
    }

    // 3. Pricing Text
    const priceText = document.getElementById('pricingText');
    if (priceText && data.pricing) {
        priceText.textContent = `${data.pricing.currency === 'INR' ? '₹' : '$'}${data.pricing.hourly_rate}/hr`;
    }

    // 4. Metric Counts
    document.getElementById('statAvailable').textContent = data.counts.available;
    document.getElementById('statOccupied').textContent = data.counts.occupied;
    document.getElementById('statEntries').textContent = data.stats.entries_today;
    document.getElementById('statExits').textContent = data.stats.exits_today;
    document.getElementById('statPeak').textContent = data.stats.peak_today;

    // 5. Render 8 Slots
    if (data.slots) {
        data.slots.forEach(slot => {
            const tile = document.getElementById(`slot-${slot.id}`);
            const badge = document.getElementById(`badge-${slot.id}`);
            const carEl = document.getElementById(`car-${slot.id}`);
            const distEl = document.getElementById(`dist-${slot.id}`);
            const timerEl = document.getElementById(`timer-${slot.id}`);

            if (!tile) return;

            // Distance
            if (slot.dist !== null && slot.dist !== undefined) {
                distEl.textContent = `Dist: ${slot.dist.toFixed(1)} cm`;
            } else {
                distEl.textContent = `Dist: -- cm`;
            }

            // State classes
            if (!data.esp32.online) {
                tile.className = 'slot-tile stale';
                badge.textContent = 'OFFLINE';
                carEl.textContent = slot.car ? `Car #${slot.car}` : '—';
                timerEl.textContent = '';
            } else if (slot.fault) {
                tile.className = 'slot-tile fault';
                badge.textContent = 'FAULT';
                carEl.textContent = 'Sensor Error';
                timerEl.textContent = '';
            } else if (slot.occupied) {
                tile.className = 'slot-tile occupied';
                badge.textContent = 'OCCUPIED';
                carEl.textContent = slot.car ? `Car #${slot.car}` : 'Unknown';

                // Find dwell time & fare
                const carObj = data.cars ? data.cars.find(c => c.car === slot.car) : null;
                if (carObj && carObj.dwell_s) {
                    const mins = Math.floor(carObj.dwell_s / 60);
                    const secs = Math.floor(carObj.dwell_s % 60);
                    timerEl.textContent = `${mins}m ${secs}s (₹${carObj.current_fare})`;
                } else {
                    timerEl.textContent = '';
                }
            } else {
                tile.className = 'slot-tile vacant';
                badge.textContent = 'FREE';
                carEl.textContent = '—';
                timerEl.textContent = '';
            }
        });
    }

    // 6. Barrier Gate Badges
    if (data.gates) {
        const entryBadge = document.getElementById('entryGateBadge');
        entryBadge.textContent = data.gates.entry.toUpperCase();
        entryBadge.className = `gate-status-pill ${data.gates.entry.toLowerCase()}`;

        const exitBadge = document.getElementById('exitGateBadge');
        exitBadge.textContent = data.gates.exit.toUpperCase();
        exitBadge.className = `gate-status-pill ${data.gates.exit.toLowerCase()}`;
    }

    // 7. Update Checkout Dropdown
    updateCheckoutDropdown(data.cars);

    // 8. Event Log Table
    if (data.events) {
        renderEventLog(data.events);
    }
}

function updateCheckoutDropdown(cars) {
    const sel = document.getElementById('checkoutCarSelect');
    if (!sel) return;

    const currentVal = sel.value;
    sel.innerHTML = '<option value="">Select Car to Checkout (1–8)...</option>';

    if (cars) {
        cars.forEach(c => {
            if (c.state === 'ENTERED' || c.state === 'PARKED') {
                const opt = document.createElement('option');
                opt.value = c.car;
                const loc = c.slot ? `Slot ${c.slot}` : 'Entered Lane';
                opt.textContent = `Car #${c.car} (${loc} — Due: ₹${c.current_fare})`;
                sel.appendChild(opt);
            }
        });
    }
    sel.value = currentVal;
}

function renderEventLog(events) {
    const tbody = document.getElementById('logTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';
    if (events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No events recorded yet.</td></tr>';
        return;
    }

    events.forEach(ev => {
        const tr = document.createElement('tr');
        
        const dt = new Date(ev.ts);
        const timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        tr.innerHTML = `
            <td>${timeStr}</td>
            <td><span class="log-badge ${ev.type}">${ev.type.toUpperCase()}</span></td>
            <td>${ev.car ? `Car #${ev.car}` : '—'}</td>
            <td>${ev.slot ? ev.slot : '—'}</td>
            <td>${ev.detail || '—'}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Commands to server
function sendGateCmd(gate, action) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            t: 'gate',
            gate: gate,
            action: action
        }));
    } else {
        // Fallback to REST API
        fetch('/api/gate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gate, action })
        }).catch(err => alert(`Error: ${err}`));
    }
}

function requestCalibration() {
    if (confirm('Run calibration? Please ensure all 8 parking bays are completely empty!')) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ t: 'cmd', cmd: 'calibrate' }));
        }
    }
}

function requestResetCounters() {
    if (confirm("Reset today's entry and exit metrics? Car parking sessions will remain intact.")) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ t: 'cmd', cmd: 'reset_counters' }));
        }
    }
}

// Manual Assignment Modal
function openAssignModal(slotId) {
    selectedSlotForAssign = slotId;
    document.getElementById('modalSlotTitle').textContent = slotId;
    
    // Set current value
    const currentSlot = currentSnapshot?.slots?.find(s => s.id === slotId);
    const sel = document.getElementById('assignCarSelect');
    sel.value = currentSlot?.car ? String(currentSlot.car) : '';

    document.getElementById('assignModal').classList.remove('hidden');
}

function closeAssignModal() {
    document.getElementById('assignModal').classList.add('hidden');
    selectedSlotForAssign = null;
}

function submitSlotAssignment() {
    if (!selectedSlotForAssign) return;
    const val = document.getElementById('assignCarSelect').value;
    const carId = val ? parseInt(val, 10) : null;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            t: 'assign',
            slot: selectedSlotForAssign,
            car: carId
        }));
    }
    closeAssignModal();
}

// Checkout & Billing Modal
function initiateCheckout() {
    const sel = document.getElementById('checkoutCarSelect');
    const carId = parseInt(sel.value, 10);
    if (!carId) {
        alert('Please select a car currently parked or inside the facility.');
        return;
    }

    const carData = currentSnapshot?.cars?.find(c => c.car === carId);
    if (!carData) return;

    pendingCheckoutCar = carId;
    document.getElementById('payCarNum').textContent = `Car #${carId}`;
    document.getElementById('paySlotNum').textContent = carData.slot || 'Lane';

    const mins = Math.floor((carData.dwell_s || 0) / 60);
    const secs = Math.floor((carData.dwell_s || 0) % 60);
    document.getElementById('payDwellTime').textContent = `${mins}m ${secs}s`;

    const curr = currentSnapshot?.pricing?.currency === 'INR' ? '₹' : '$';
    document.getElementById('payRate').textContent = `Base: ${curr}${currentSnapshot?.pricing?.base_fee || 10} + ${curr}${currentSnapshot?.pricing?.hourly_rate || 20}/hr`;
    document.getElementById('payTotalAmount').textContent = `${curr}${(carData.current_fare || 0).toFixed(2)}`;

    document.getElementById('paymentModal').classList.remove('hidden');
}

function closePaymentModal() {
    document.getElementById('paymentModal').classList.add('hidden');
    pendingCheckoutCar = null;
}

function confirmPaymentAndOpenGate() {
    if (!pendingCheckoutCar) return;

    fetch('/api/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car: pendingCheckoutCar, method: 'UPI' })
    })
    .then(res => res.json())
    .then(data => {
        if (data.ok) {
            alert(`Payment Approved!\nReceipt ID: ${data.receipt_id}\nFare: ${data.fare} ${data.currency}\nExit gate opening!`);
            closePaymentModal();
        } else {
            alert(`Checkout Error: ${data.reason}`);
        }
    })
    .catch(err => alert(`Network Error: ${err}`));
}

// Sim Modal
function openSimModal() {
    document.getElementById('simModal').classList.remove('hidden');
}

function closeSimModal() {
    document.getElementById('simModal').classList.add('hidden');
}

function simulateArrival() {
    const carId = parseInt(document.getElementById('simCarSelect').value, 10);
    fetch('/api/entry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car: carId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.ok) {
            alert(`Simulation Success!\nCar #${carId} approved for entry!\nEntry gate opening.`);
        } else {
            alert(`Entry Refused: ${data.reason}`);
        }
    })
    .catch(err => alert(`Simulation Error: ${err}`));
}

// Start
connectWebSocket();
