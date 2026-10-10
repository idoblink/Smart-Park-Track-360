/**
 * ParkTrack 360 — Administrator Operations Console Script (admin.js)
 * Barrier gate overrides, calibration trigger, slot reassignment, and event audit.
 */

(function () {
  'use strict';

  // Check Auth Token
  const token = sessionStorage.getItem('pts_admin_token');
  if (!token) {
    window.location.href = '/admin/login';
    return;
  }

  // Logout Handler
  const btnLogout = document.getElementById('btnLogout');
  if (btnLogout) {
    btnLogout.addEventListener('click', () => {
      sessionStorage.removeItem('pts_admin_token');
      window.location.href = '/admin/login';
    });
  }

  let ws = null;
  let currentSnapshot = null;
  let selectedSlotForAssign = null;

  // DOM Elements
  const esp32Dot = document.getElementById('esp32Dot');
  const esp32StatusText = document.getElementById('esp32StatusText');
  const esp32Details = document.getElementById('esp32Details');

  const entryGateBadge = document.getElementById('entryGateBadge');
  const exitGateBadge = document.getElementById('exitGateBadge');
  const calBadge = document.getElementById('calBadge');

  const adminOccupancySummary = document.getElementById('adminOccupancySummary');
  const adminSlotsGrid = document.getElementById('adminSlotsGrid');
  const adminCarsTableBody = document.getElementById('adminCarsTableBody');
  const adminAuditFeed = document.getElementById('adminAuditFeed');

  // Gate Controls
  document.getElementById('btnOpenEntryGate')?.addEventListener('click', () => sendGateCmd('entry', 'open'));
  document.getElementById('btnCloseEntryGate')?.addEventListener('click', () => sendGateCmd('entry', 'close'));
  document.getElementById('btnOpenExitGate')?.addEventListener('click', () => sendGateCmd('exit', 'open'));
  document.getElementById('btnCloseExitGate')?.addEventListener('click', () => sendGateCmd('exit', 'close'));

  // Maintenance Controls
  document.getElementById('btnTriggerCalibrate')?.addEventListener('click', () => {
    if (confirm('Trigger sensor baseline calibration? Ensure all 8 bays are completely empty.')) {
      sendWsCmd('calibrate');
    }
  });

  document.getElementById('btnResetCounters')?.addEventListener('click', () => {
    if (confirm('Reset today\'s entry and exit audit counters?')) {
      sendWsCmd('reset_counters');
    }
  });

  // Modal: Manual Slot Assignment
  const modalAssign = document.getElementById('modalAssign');
  const btnCloseAssignModal = document.getElementById('btnCloseAssignModal');
  const btnCancelAssignment = document.getElementById('btnCancelAssignment');
  const btnSaveAssignment = document.getElementById('btnSaveAssignment');
  const modalAssignSlotTitle = document.getElementById('modalAssignSlotTitle');
  const modalAssignCarSelect = document.getElementById('modalAssignCarSelect');

  function openAssignModal(slotId, currentCar) {
    selectedSlotForAssign = slotId;
    if (modalAssignSlotTitle) modalAssignSlotTitle.textContent = `ASSIGN SLOT ${slotId}`;
    if (modalAssignCarSelect) modalAssignCarSelect.value = currentCar ? String(currentCar) : '';
    if (modalAssign) modalAssign.classList.add('active');
  }

  function closeAssignModal() {
    if (modalAssign) modalAssign.classList.remove('active');
    selectedSlotForAssign = null;
  }

  btnCloseAssignModal?.addEventListener('click', closeAssignModal);
  btnCancelAssignment?.addEventListener('click', closeAssignModal);

  btnSaveAssignment?.addEventListener('click', async () => {
    if (!selectedSlotForAssign) return;
    const val = modalAssignCarSelect.value;
    const carId = val ? parseInt(val, 10) : null;

    try {
      const res = await fetch('/api/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: selectedSlotForAssign, car: carId })
      });
      if (res.ok) {
        closeAssignModal();
      } else {
        alert('Failed to reassign slot');
      }
    } catch (e) {
      console.error('Assign error:', e);
    }
  });



  // Connect WebSocket
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/ui`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[Admin] Connected to state engine.');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.t === 'snapshot') {
          handleSnapshot(msg);
        }
      } catch (e) {
        console.error('[Admin] JSON parse error:', e);
      }
    };

    ws.onclose = () => {
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  function sendGateCmd(gate, action) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        t: 'gate',
        gate: gate,
        action: action,
        hold_ms: 5000,
        req_id: `admin_${gate}_${Date.now()}`
      }));
    } else {
      fetch('/api/gate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gate, action, hold_ms: 5000 })
      }).catch(console.error);
    }
  }

  function sendWsCmd(cmd) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ t: 'cmd', cmd: cmd }));
    }
  }

  // Handle Snapshot
  function handleSnapshot(snap) {
    currentSnapshot = snap;

    // ESP32 Health
    const isOnline = snap.esp32?.online;
    if (esp32Dot) {
      esp32Dot.style.background = isOnline ? 'var(--emerald-free)' : '#ef4444';
      esp32Dot.style.boxShadow = isOnline ? '0 0 10px var(--emerald-free)' : 'none';
    }
    if (esp32StatusText) {
      esp32StatusText.textContent = isOnline ? 'ESP32: Online' : 'ESP32: Offline / Standalone';
    }
    if (esp32Details) {
      esp32Details.textContent = `IP: ${snap.esp32?.ip || '0.0.0.0'} • FW: ${snap.esp32?.fw || '1.1.0'}`;
    }

    // Gate States
    if (entryGateBadge) {
      const eState = snap.gates?.entry || 'closed';
      entryGateBadge.textContent = eState.toUpperCase();
      entryGateBadge.className = `slot-status-pill ${eState === 'closed' ? 'vacant' : 'occupied'}`;
    }
    if (exitGateBadge) {
      const xState = snap.gates?.exit || 'closed';
      exitGateBadge.textContent = xState.toUpperCase();
      exitGateBadge.className = `slot-status-pill ${xState === 'closed' ? 'vacant' : 'occupied'}`;
    }

    // Calibration
    if (calBadge) {
      const isCal = snap.esp32?.calibrated;
      calBadge.textContent = isCal ? 'CALIBRATED' : 'UNCALIBRATED';
      calBadge.style.color = isCal ? '#38bdf8' : '#f59e0b';
    }

    // Occupancy Summary
    if (adminOccupancySummary) {
      adminOccupancySummary.textContent = `Total: ${snap.counts?.total || 8} • Occ: ${snap.counts?.occupied || 0} • Free: ${snap.counts?.available || 0}`;
    }

    // Render Slots Grid
    renderSlots(snap.slots);

    // Render Cars Table
    renderCarsTable(snap.cars);

    // Render Audit Events
    renderAuditEvents(snap.events);
  }

  function renderSlots(slots) {
    if (!adminSlotsGrid || !slots) return;

    // Ground floor first (G1-G4), First floor second (F1-F4)
    const sorted = [...slots].sort((a, b) => {
      if (a.floor === 'G' && b.floor !== 'G') return -1;
      if (a.floor !== 'G' && b.floor === 'G') return 1;
      return a.id.localeCompare(b.id);
    });

    adminSlotsGrid.innerHTML = sorted.map(s => {
      const isOcc = s.occupied;
      const isFault = s.fault;
      const statusClass = isFault ? 'fault' : (isOcc ? 'occupied' : 'vacant');
      const statusLabel = isFault ? 'FAULT' : (isOcc ? `CAR #${s.car || '?'}` : 'VACANT');
      const dist = s.dist !== null && s.dist !== undefined ? `${s.dist.toFixed(1)} cm` : 'Active';

      return `
        <div class="slot-tile ${statusClass}" style="min-height: 120px; padding: 1rem; cursor: pointer;" onclick="window._openAssign('${s.id}', ${s.car || 'null'})" title="Click to override slot assignment">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="slot-id" style="font-size: 1.8rem;">${s.id}</span>
            <span class="slot-status-pill ${statusClass}" style="font-size: 0.6rem; padding: 0.2rem 0.5rem;">${statusLabel}</span>
          </div>
          <div style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem;">
            Dist: ${dist}
          </div>
        </div>
      `;
    }).join('');
  }

  window._openAssign = (slotId, currentCar) => {
    openAssignModal(slotId, currentCar);
  };

  function renderCarsTable(cars) {
    if (!adminCarsTableBody || !cars) return;

    adminCarsTableBody.innerHTML = cars.map(c => {
      const isInside = c.state !== 'OUTSIDE';
      const stateBadge = isInside 
        ? `<span class="slot-status-pill occupied" style="font-size:0.65rem;">${c.state}</span>`
        : `<span class="slot-status-pill vacant" style="font-size:0.65rem;">OUTSIDE</span>`;

      const slotText = c.slot || '-';
      const dwellText = isInside ? formatDuration(c.dwell_s) : '-';
      const fareText = isInside ? `₹${(c.current_fare || 0).toFixed(2)}` : '₹0.00';

      const actionBtn = isInside 
        ? `<button class="btn btn-outline-gold btn-sm" onclick="window._checkoutCar(${c.car})" style="padding: 0.25rem 0.6rem; font-size: 0.68rem;">Clear & Open Exit</button>`
        : `<button class="btn btn-dark btn-sm" onclick="window._enterCar(${c.car})" style="padding: 0.25rem 0.6rem; font-size: 0.68rem;">Force Entry</button>`;

      return `
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
          <td style="padding: 0.6rem 0.5rem; font-weight: 700; color: #fff;">Car #${c.car}</td>
          <td style="padding: 0.6rem 0.5rem;">${stateBadge}</td>
          <td style="padding: 0.6rem 0.5rem; font-family: var(--font-mono);">${slotText}</td>
          <td style="padding: 0.6rem 0.5rem; font-family: var(--font-mono);">${dwellText}</td>
          <td style="padding: 0.6rem 0.5rem; font-family: var(--font-mono); color: var(--gold-primary);">${fareText}</td>
          <td style="padding: 0.6rem 0.5rem; text-align: right;">${actionBtn}</td>
        </tr>
      `;
    }).join('');
  }

  window._checkoutCar = async (carId) => {
    if (confirm(`Clear Car #${carId} and open exit barrier?`)) {
      try {
        const res = await fetch('/api/billing/checkout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ car: carId, method: 'ADMIN_CLEAR' })
        });
        const data = await res.json();
        if (data.ok) {
          alert(`Car #${carId} cleared. Exit barrier opening.`);
        }
      } catch (e) {
        alert('Checkout error');
      }
    }
  };

  window._enterCar = async (carId) => {
    try {
      const res = await fetch('/api/entry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car: carId })
      });
      const data = await res.json();
      if (data.ok) {
        alert(`Car #${carId} admitted. Entry gate opened.`);
      } else {
        alert(`Could not admit: ${data.reason}`);
      }
    } catch (e) {
      alert('Entry error');
    }
  };

  function renderAuditEvents(events) {
    if (!adminAuditFeed || !events) return;

    if (events.length === 0) {
      adminAuditFeed.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 1rem;">No recent audit events.</div>';
      return;
    }

    adminAuditFeed.innerHTML = events.slice(0, 30).map(ev => {
      const timeStr = formatEventTime(ev.ts);
      let color = 'var(--text-secondary)';
      if (ev.type === 'entry') color = 'var(--emerald-free)';
      else if (ev.type === 'exit') color = '#38bdf8';
      else if (ev.type === 'deny') color = 'var(--crimson-occupied)';
      else if (ev.type === 'manual_gate') color = 'var(--gold-primary)';

      const carTag = ev.car ? `[Car #${ev.car}]` : '';
      const slotTag = ev.slot ? `[${ev.slot}]` : '';

      return `
        <div class="audit-item">
          <span style="color: var(--text-muted); font-size: 0.7rem; flex-shrink: 0;">${timeStr}</span>
          <span style="color: ${color}; font-weight: 700; text-transform: uppercase;">${ev.type}</span>
          <span style="color: #fff;">${carTag} ${slotTag} ${ev.detail || ''}</span>
        </div>
      `;
    }).join('');
  }

  function formatEventTime(ts) {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
      return ts;
    }
  }

  function formatDuration(sec) {
    const s = Math.floor(sec || 0);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // Initial Fetch & Connect
  fetch('/api/snapshot').then(r => r.json()).then(handleSnapshot).catch(console.error);
  connectWebSocket();

})();
