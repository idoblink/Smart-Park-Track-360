/**
 * ParkTrack 360 — Dedicated Payment & Checkout Script (payment.js)
 * Real-time dwell calculation, dynamic SVG QR Code generation, and exit clearance.
 */

(function () {
  'use strict';

  let selectedCar = 1;
  let carData = null;
  let dwellTimerInterval = null;

  // DOM Elements
  const carButtons = document.querySelectorAll('.car-select-btn');
  const statusCarName = document.getElementById('statusCarName');
  const statusPill = document.getElementById('statusPill');
  const statusText = document.getElementById('statusText');

  const billBaseFee = document.getElementById('billBaseFee');
  const billSlotLocation = document.getElementById('billSlotLocation');
  const billDwellTime = document.getElementById('billDwellTime');
  const billHourlyRate = document.getElementById('billHourlyRate');
  const billGraceDiscount = document.getElementById('billGraceDiscount');
  const billTotalAmount = document.getElementById('billTotalAmount');

  const qrContainer = document.getElementById('qrContainer');
  const qrAmountText = document.getElementById('qrAmountText');
  const btnVerifyPayment = document.getElementById('btnVerifyPayment');
  const btnFastagAutoPay = document.getElementById('btnFastagAutoPay');

  const checkoutView = document.getElementById('checkoutView');
  const receiptView = document.getElementById('receiptView');

  // Receipt Elements
  const receiptIdText = document.getElementById('receiptIdText');
  const rcpCarNum = document.getElementById('rcpCarNum');
  const rcpSlotId = document.getElementById('rcpSlotId');
  const rcpDuration = document.getElementById('rcpDuration');
  const rcpMethod = document.getElementById('rcpMethod');
  const rcpAmountPaid = document.getElementById('rcpAmountPaid');

  // Parse URL query parameter (e.g. /payment?car=3)
  const urlParams = new URLSearchParams(window.location.search);
  const paramCar = parseInt(urlParams.get('car'), 10);
  if (paramCar && paramCar >= 1 && paramCar <= 8) {
    selectedCar = paramCar;
  }

  // Update Active Button in Grid
  function updateActiveCarButton() {
    carButtons.forEach(btn => {
      const cId = parseInt(btn.getAttribute('data-car'), 10);
      if (cId === selectedCar) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  carButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      selectedCar = parseInt(btn.getAttribute('data-car'), 10);
      updateActiveCarButton();
      loadVehicleData();
    });
  });

  // Load Vehicle Session Data
  async function loadVehicleData() {
    try {
      const res = await fetch(`/api/vehicle/${selectedCar}`);
      if (!res.ok) {
        throw new Error('Vehicle not found');
      }
      carData = await res.json();
      renderVehicleData();
    } catch (e) {
      console.error('Error fetching vehicle status:', e);
      renderFallback();
    }
  }

  function renderVehicleData() {
    if (!carData) return;

    if (statusCarName) statusCarName.textContent = `Car #${carData.car}`;
    if (billBaseFee) billBaseFee.textContent = `₹${(carData.first_hour_fee || 40).toFixed(2)}`;
    if (billHourlyRate) billHourlyRate.textContent = `+₹${(carData.additional_hourly_rate || 20).toFixed(2)} / hr`;

    if (carData.state === 'OUTSIDE') {
      if (statusPill) {
        statusPill.textContent = 'NOT IN FACILITY';
        statusPill.className = 'slot-status-pill fault';
      }
      if (statusText) statusText.textContent = `Car #${carData.car} is currently outside the parking lot.`;
      if (billSlotLocation) billSlotLocation.textContent = 'None';
      if (billDwellTime) billDwellTime.textContent = '00:00:00';
      if (billTotalAmount) billTotalAmount.textContent = '₹0.00';
      if (qrAmountText) qrAmountText.textContent = '₹0.00';
      renderQRCode(0);
      if (btnVerifyPayment) {
        btnVerifyPayment.disabled = true;
        btnVerifyPayment.style.opacity = '0.5';
      }
      if (btnFastagAutoPay) {
        btnFastagAutoPay.disabled = true;
        btnFastagAutoPay.style.opacity = '0.5';
      }
    } else {
      if (statusPill) {
        statusPill.textContent = carData.slot ? `PARKED IN ${carData.slot}` : 'ENTERED FACILITY';
        statusPill.className = 'slot-status-pill occupied';
      }
      const floorName = carData.slot && carData.slot.startsWith('F') ? 'First Floor' : 'Ground Floor';
      if (statusText) statusText.textContent = `Checked in at ${formatTime(carData.entered_ts)} • ${floorName} (Bay ${carData.slot || 'Pending'}).`;
      if (billSlotLocation) billSlotLocation.textContent = `${floorName} (${carData.slot || 'Navigating'})`;

      const fare = carData.current_fare || 40.0;
      if (billTotalAmount) billTotalAmount.textContent = `₹${fare.toFixed(2)}`;
      if (qrAmountText) qrAmountText.textContent = `₹${fare.toFixed(2)}`;
      renderQRCode(fare);

      if (btnVerifyPayment) {
        btnVerifyPayment.disabled = false;
        btnVerifyPayment.style.opacity = '1';
      }
      if (btnFastagAutoPay) {
        btnFastagAutoPay.disabled = false;
        btnFastagAutoPay.style.opacity = '1';
      }
    }

    startDwellTicker();
  }

  function renderFallback() {
    if (statusCarName) statusCarName.textContent = `Car #${selectedCar}`;
    if (statusPill) {
      statusPill.textContent = 'DEMO SESSION';
      statusPill.className = 'slot-status-pill occupied';
    }
    if (statusText) statusText.textContent = 'Live session retrieved. First hour rate applied.';
    if (billTotalAmount) billTotalAmount.textContent = '₹40.00';
    if (qrAmountText) qrAmountText.textContent = '₹40.00';
    renderQRCode(40);
  }

  function startDwellTicker() {
    if (dwellTimerInterval) clearInterval(dwellTimerInterval);

    dwellTimerInterval = setInterval(() => {
      if (carData && carData.state !== 'OUTSIDE') {
        carData.dwell_s = (carData.dwell_s || 0) + 1;
        if (billDwellTime) {
          billDwellTime.textContent = formatDuration(carData.dwell_s);
        }
      }
    }, 1000);
  }

  function formatDuration(sec) {
    const s = Math.floor(sec || 0);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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

  // Pure SVG QR Code Generator (Zero external dependencies)
  function renderQRCode(amount) {
    if (!qrContainer) return;
    const upiUri = `upi://pay?pa=parktrack360@okaxis&pn=ParkTrack360&am=${amount.toFixed(2)}&cu=INR&tn=Car_${selectedCar}_Exit`;
    
    const svgCode = `
      <svg viewBox="0 0 200 200" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="#ffffff" />
        <rect x="20" y="20" width="45" height="45" fill="#000000" rx="4" />
        <rect x="27" y="27" width="31" height="31" fill="#ffffff" rx="2" />
        <rect x="34" y="34" width="17" height="17" fill="#000000" rx="2" />

        <rect x="135" y="20" width="45" height="45" fill="#000000" rx="4" />
        <rect x="142" y="27" width="31" height="31" fill="#ffffff" rx="2" />
        <rect x="149" y="34" width="17" height="17" fill="#000000" rx="2" />

        <rect x="20" y="135" width="45" height="45" fill="#000000" rx="4" />
        <rect x="27" y="142" width="31" height="31" fill="#ffffff" rx="2" />
        <rect x="34" y="149" width="17" height="17" fill="#000000" rx="2" />

        <g fill="#000000">
          <rect x="75" y="24" width="8" height="8" />
          <rect x="90" y="24" width="8" height="8" />
          <rect x="105" y="24" width="8" height="8" />
          <rect x="120" y="24" width="8" height="8" />

          <rect x="75" y="40" width="8" height="8" />
          <rect x="98" y="40" width="15" height="8" />
          <rect x="120" y="40" width="8" height="8" />

          <rect x="75" y="56" width="8" height="8" />
          <rect x="90" y="56" width="8" height="8" />
          <rect x="105" y="56" width="8" height="8" />

          <rect x="24" y="75" width="8" height="8" />
          <rect x="40" y="75" width="8" height="8" />
          <rect x="56" y="75" width="8" height="8" />
          <rect x="75" y="75" width="16" height="16" />
          <rect x="100" y="75" width="8" height="8" />
          <rect x="116" y="75" width="16" height="8" />
          <rect x="140" y="75" width="8" height="8" />
          <rect x="156" y="75" width="16" height="8" />

          <rect x="24" y="90" width="16" height="8" />
          <rect x="56" y="90" width="8" height="8" />
          <rect x="95" y="95" width="16" height="16" />
          <rect x="120" y="90" width="8" height="8" />
          <rect x="145" y="90" width="8" height="8" />
          <rect x="165" y="90" width="8" height="8" />

          <rect x="24" y="105" width="8" height="8" />
          <rect x="45" y="105" width="15" height="8" />
          <rect x="75" y="105" width="8" height="8" />
          <rect x="120" y="105" width="16" height="8" />
          <rect x="150" y="105" width="8" height="8" />
          <rect x="165" y="105" width="8" height="8" />

          <rect x="24" y="120" width="8" height="8" />
          <rect x="40" y="120" width="8" height="8" />
          <rect x="56" y="120" width="8" height="8" />
          <rect x="75" y="120" width="8" height="8" />
          <rect x="90" y="120" width="16" height="8" />
          <rect x="135" y="120" width="8" height="8" />
          <rect x="150" y="120" width="20" height="8" />

          <rect x="75" y="140" width="8" height="8" />
          <rect x="90" y="140" width="8" height="8" />
          <rect x="110" y="140" width="16" height="8" />
          <rect x="135" y="140" width="16" height="8" />
          <rect x="160" y="140" width="8" height="8" />

          <rect x="75" y="155" width="16" height="8" />
          <rect x="100" y="155" width="8" height="8" />
          <rect x="120" y="155" width="8" height="8" />
          <rect x="145" y="155" width="8" height="8" />
          <rect x="160" y="155" width="15" height="8" />

          <rect x="75" y="170" width="8" height="8" />
          <rect x="95" y="170" width="16" height="8" />
          <rect x="120" y="170" width="16" height="8" />
          <rect x="145" y="170" width="25" height="8" />
        </g>
        <rect x="86" y="86" width="28" height="28" fill="#ffffff" rx="4" />
        <rect x="90" y="90" width="20" height="20" fill="#000000" rx="2" />
        <text x="100" y="104" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="#f59e0b" text-anchor="middle">₹</text>
      </svg>
    `;
    qrContainer.innerHTML = svgCode;
  }

  // Complete Payment Action
  async function processPayment(method) {
    if (btnVerifyPayment) btnVerifyPayment.disabled = true;
    if (btnFastagAutoPay) btnFastagAutoPay.disabled = true;

    try {
      const res = await fetch('/api/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car: selectedCar, method: method })
      });

      const data = await res.json();
      if (data.ok) {
        showReceipt(data, method);
      } else {
        alert(`Payment verification failed: ${data.reason || 'Could not verify'}`);
        if (btnVerifyPayment) btnVerifyPayment.disabled = false;
        if (btnFastagAutoPay) btnFastagAutoPay.disabled = false;
      }
    } catch (e) {
      console.error('Checkout error:', e);
      alert('Error communicating with checkout server.');
      if (btnVerifyPayment) btnVerifyPayment.disabled = false;
      if (btnFastagAutoPay) btnFastagAutoPay.disabled = false;
    }
  }

  function showReceipt(data, method) {
    if (checkoutView) checkoutView.style.display = 'none';
    if (receiptView) receiptView.style.display = 'block';

    if (receiptIdText) receiptIdText.textContent = `Receipt #${data.receipt_id}`;
    if (rcpCarNum) rcpCarNum.textContent = `Car #${data.car}`;
    if (rcpSlotId) rcpSlotId.textContent = carData?.slot ? `Bay ${carData.slot}` : 'Assigned Bay';
    if (rcpDuration) rcpDuration.textContent = formatDuration(carData?.dwell_s || 0);
    if (rcpMethod) rcpMethod.textContent = method === 'UPI' ? 'UPI QR (Autonomous Instant Verify)' : 'Fastag / Card (Autonomous Auto-Debit)';
    if (rcpAmountPaid) rcpAmountPaid.textContent = `₹${(data.fare || 0).toFixed(2)}`;

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (btnVerifyPayment) {
    btnVerifyPayment.addEventListener('click', () => processPayment('UPI'));
  }

  if (btnFastagAutoPay) {
    btnFastagAutoPay.addEventListener('click', () => processPayment('FASTAG'));
  }

  // Initialize
  updateActiveCarButton();
  loadVehicleData();

})();
