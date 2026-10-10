/**
 * ParkTrack 360 — Public User Portal Script (user.js)
 * Real-time WebSocket sync, interactive 2-floor slot matrix, and vehicle locator tool.
 */

(function () {
  'use strict';

  let currentSnapshot = null;
  let activeFilter = 'all';
  let selectedVehicleId = 1;

  // DOM Elements
  const elTotalSlots = document.getElementById('valTotalSlots');
  const elAvailSlots = document.getElementById('valAvailSlots');
  const elOccSlots = document.getElementById('valOccSlots');
  const elOccupancyBar = document.getElementById('occupancyBar');
  const elOccupancyText = document.getElementById('occupancyText');
  const elOccupancyPercent = document.getElementById('occupancyPercent');

  const elGridFirstFloor = document.getElementById('gridFirstFloor');
  const elGridGroundFloor = document.getElementById('gridGroundFloor');
  const elStatFirstFloor = document.getElementById('statFirstFloor');
  const elStatGroundFloor = document.getElementById('statGroundFloor');

  const cardFloorFirst = document.getElementById('cardFloorFirst');
  const cardFloorGround = document.getElementById('cardFloorGround');

  const heroVideo = document.getElementById('heroVideo');
  const btnToggleVideo = document.getElementById('btnToggleVideo');
  const videoBtnIcon = document.getElementById('videoBtnIcon');
  const videoBtnText = document.getElementById('videoBtnText');

  // Video Toggle Logic
  if (btnToggleVideo && heroVideo) {
    btnToggleVideo.addEventListener('click', () => {
      if (heroVideo.paused) {
        heroVideo.play().then(() => {
          videoBtnIcon.textContent = '❚❚';
          videoBtnText.textContent = 'Pause Video';
        }).catch(() => {});
      } else {
        heroVideo.pause();
        videoBtnIcon.textContent = '▶';
        videoBtnText.textContent = 'Play Video';
      }
    });
  }

  // Filter Tabs
  const floorTabs = document.querySelectorAll('.floor-tab');
  floorTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      floorTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeFilter = tab.getAttribute('data-filter');
      applyFilter();
    });
  });

  function applyFilter() {
    if (activeFilter === 'ground') {
      cardFloorGround.style.display = 'block';
      cardFloorFirst.style.display = 'none';
    } else if (activeFilter === 'first') {
      cardFloorGround.style.display = 'none';
      cardFloorFirst.style.display = 'block';
    } else {
      cardFloorGround.style.display = 'block';
      cardFloorFirst.style.display = 'block';
    }

    if (currentSnapshot) {
      renderSlots(currentSnapshot.slots);
    }
  }

  // WebSocket Client
  let ws = null;
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/ui`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[ParkTrack UI] Connected to live state feed.');
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.t === 'snapshot') {
          handleSnapshot(msg);
        }
      } catch (e) {
        console.error('[ParkTrack UI] JSON parse error:', e);
      }
    };

    ws.onclose = () => {
      console.warn('[ParkTrack UI] WebSocket disconnected. Reconnecting in 3s...');
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  // REST Fallback Initial Fetch
  async function fetchInitialSnapshot() {
    try {
      const res = await fetch('/api/snapshot');
      if (res.ok) {
        const data = await res.json();
        handleSnapshot(data);
      }
    } catch (e) {
      console.error('[ParkTrack UI] Initial fetch error:', e);
    }
  }

  // Handle Snapshot updates
  function handleSnapshot(snap) {
    currentSnapshot = snap;

    // 1. Update the 3 Mandatory Counters
    const total = snap.counts?.total || 8;
    const occupied = snap.counts?.occupied || 0;
    const available = snap.counts?.available || 0;

    if (elTotalSlots) elTotalSlots.textContent = total;
    if (elAvailSlots) elAvailSlots.textContent = available;
    if (elOccSlots) elOccSlots.textContent = occupied;

    const occPercent = Math.round((occupied / total) * 100);
    if (elOccupancyPercent) elOccupancyPercent.textContent = `${occPercent}%`;
    if (elOccupancyBar) elOccupancyBar.style.width = `${occPercent}%`;
    if (elOccupancyText) {
      if (available === 0) {
        elOccupancyText.textContent = 'Lot Full • No bays currently available';
        elOccupancyBar.style.background = 'var(--crimson-occupied)';
      } else {
        elOccupancyText.textContent = `${available} of ${total} Bays Free (${100 - occPercent}% Vacant)`;
        elOccupancyBar.style.background = '#0f172a';
      }
    }

    // 2. Render Slots
    renderSlots(snap.slots);

    // 3. Update Vehicle Locator if a vehicle is selected
    updateVehicleLocator();
  }

  function renderSlots(slots) {
    if (!slots) return;

    let firstFloorSlots = [];
    let groundFloorSlots = [];

    let ffFree = 0, ffOcc = 0;
    let gfFree = 0, gfOcc = 0;

    slots.forEach(s => {
      if (s.floor === 'F') {
        firstFloorSlots.push(s);
        if (s.occupied) ffOcc++; else ffFree++;
      } else {
        groundFloorSlots.push(s);
        if (s.occupied) gfOcc++; else gfFree++;
      }
    });

    if (elStatFirstFloor) {
      elStatFirstFloor.innerHTML = `<span style="color:var(--emerald-free);">${ffFree} Free</span> • <span style="color:var(--crimson-occupied);">${ffOcc} Occupied</span>`;
    }
    if (elStatGroundFloor) {
      elStatGroundFloor.innerHTML = `<span style="color:var(--emerald-free);">${gfFree} Free</span> • <span style="color:var(--crimson-occupied);">${gfOcc} Occupied</span>`;
    }

    // Filter slots if 'vacant' filter is active
    let displayFF = firstFloorSlots;
    let displayGF = groundFloorSlots;

    if (activeFilter === 'vacant') {
      displayFF = displayFF.filter(s => !s.occupied);
      displayGF = displayGF.filter(s => !s.occupied);
    }

    if (elGridFirstFloor) {
      elGridFirstFloor.innerHTML = displayFF.map(createSlotHTML).join('');
    }
    if (elGridGroundFloor) {
      elGridGroundFloor.innerHTML = displayGF.map(createSlotHTML).join('');
    }
  }

  function createSlotHTML(slot) {
    const isOccupied = slot.occupied;
    const isFault = slot.fault;
    const statusClass = isFault ? 'fault' : (isOccupied ? 'occupied' : 'vacant');
    const statusLabel = isFault ? 'FAULT' : (isOccupied ? 'OCCUPIED' : 'VACANT • PULL IN');

    const carBadge = isOccupied && slot.car 
      ? `<div class="slot-car-tag">
           <span style="color:var(--text-muted); font-size:0.75rem;">VEHICLE:</span>
           <span class="slot-car-pill">CAR #${slot.car}</span>
         </div>`
      : `<div class="slot-car-tag">
           <span style="color:var(--emerald-free); font-size:0.75rem; font-weight:700;">READY TO PARK</span>
         </div>`;

    const distText = slot.dist !== null && slot.dist !== undefined
      ? `Sensor: ${slot.dist.toFixed(1)} cm`
      : `Sensor: Active`;

    return `
      <div class="slot-tile ${statusClass}">
        <div class="slot-tile-top">
          <div>
            <div class="slot-id">${slot.id}</div>
            <div style="font-size:0.72rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.1em;">
              ${slot.floor === 'F' ? 'First Floor' : 'Ground Floor'}
            </div>
          </div>
          <span class="slot-status-pill ${statusClass}">${statusLabel}</span>
        </div>
        <div class="slot-tile-bottom">
          ${carBadge}
          <div class="slot-dist-readout">${distText}</div>
        </div>
      </div>
    `;
  }

  // Vehicle Locator Tool
  const chips = document.querySelectorAll('.car-select-btn');
  const elResult = document.getElementById('finderResult');
  const elResultTitle = document.getElementById('resultTitle');
  const elResultDesc = document.getElementById('resultDesc');
  const elResultFare = document.getElementById('resultFare');
  const elResultDwell = document.getElementById('resultDwell');
  const elResultPayBtn = document.getElementById('resultPayBtn');
  const elResultTag = document.getElementById('resultTag');

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedVehicleId = parseInt(chip.getAttribute('data-car'), 10);
      updateVehicleLocator();
    });
  });

  function updateVehicleLocator() {
    if (!currentSnapshot || !currentSnapshot.cars) return;
    const carData = currentSnapshot.cars.find(c => c.car === selectedVehicleId);
    if (!carData) return;

    if (elResult) elResult.classList.add('active');
    if (elResultTitle) elResultTitle.textContent = `Car #${selectedVehicleId}`;

    if (carData.state === 'OUTSIDE') {
      if (elResultTag) elResultTag.textContent = 'VEHICLE STATUS';
      if (elResultDesc) elResultDesc.textContent = `Car #${selectedVehicleId} is currently outside the facility (not checked in).`;
      if (elResultFare) elResultFare.textContent = '₹0.00';
      if (elResultDwell) elResultDwell.textContent = 'Status: Outside Facility';
      if (elResultPayBtn) {
        elResultPayBtn.style.display = 'none';
      }
    } else {
      if (elResultTag) elResultTag.textContent = 'VEHICLE LOCATED';
      const slotText = carData.slot ? `Safely parked in Slot ${carData.slot}` : 'Entered facility (navigating to bay)';
      if (elResultDesc) elResultDesc.textContent = `${slotText} since ${formatTime(carData.entered_ts)}.`;
      if (elResultFare) elResultFare.textContent = `₹${(carData.current_fare || 0).toFixed(2)}`;
      
      const dwellFormatted = formatDuration(carData.dwell_s || 0);
      if (elResultDwell) elResultDwell.textContent = `Dwell Time: ${dwellFormatted}`;
      if (elResultPayBtn) {
        elResultPayBtn.style.display = 'inline-flex';
        elResultPayBtn.href = `/payment?car=${selectedVehicleId}`;
      }
    }
  }

  function formatTime(isoStr) {
    if (!isoStr) return 'N/A';
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return isoStr;
    }
  }

  function formatDuration(sec) {
    const s = Math.floor(sec || 0);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // Initialize
  fetchInitialSnapshot();
  connectWebSocket();

  // Tick live timers every second
  setInterval(() => {
    if (currentSnapshot && currentSnapshot.cars) {
      currentSnapshot.cars.forEach(c => {
        if (c.state !== 'OUTSIDE') {
          c.dwell_s = (c.dwell_s || 0) + 1;
        }
      });
      updateVehicleLocator();
    }
  }, 1000);

})();
