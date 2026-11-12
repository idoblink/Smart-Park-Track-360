/**
 * ParkTrack 360 — Autonomous Payment & QR Settlement Script (payment.js)
 * Real-time dwell calculation, dynamic scannable UPI QR code generation,
 * Razorpay Checkout SDK integration, and automated exit barrier gate clearance.
 */

(function () {
  'use strict';

  let selectedCar = null;
  let carData = null;
  let activeCarsList = [];
  let currentOrderData = null;
  let dwellTimerInterval = null;

  // DOM Elements
  const checkoutCarGrid = document.getElementById('checkoutCarGrid');
  const activeCountBadge = document.getElementById('activeCountBadge');
  const statusCarName = document.getElementById('statusCarName');
  const statusPill = document.getElementById('statusPill');
  const statusText = document.getElementById('statusText');

  const billBaseFee = document.getElementById('billBaseFee');
  const billSlotLocation = document.getElementById('billSlotLocation');
  const billDwellTime = document.getElementById('billDwellTime');
  const billHourlyRate = document.getElementById('billHourlyRate');
  const billTotalAmount = document.getElementById('billTotalAmount');

  const qrContainer = document.getElementById('qrContainer');
  const qrAmountText = document.getElementById('qrAmountText');
  const upiIdDisplay = document.getElementById('upiIdDisplay');
  const btnPhonePePay = document.getElementById('btnPhonePePay');
  const btnRazorpayPay = document.getElementById('btnRazorpayPay');
  const btnVerifyManual = document.getElementById('btnVerifyManual');

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

  // 1. Fetch Active Cars (Only vehicles inside the facility)
  async function loadActiveCars() {
    try {
      const res = await fetch('/api/active-cars');
      if (!res.ok) throw new Error('Failed to load active vehicles');
      const data = await res.json();
      activeCarsList = data.active_cars || [];
      const carAtExit = data.car_at_exit;

      renderCarSelector(activeCarsList, carAtExit);

      // Select target car: either from URL, or car at exit, or first available inside
      if (paramCar && activeCarsList.some(c => c.car === paramCar)) {
        selectedCar = paramCar;
      } else if (carAtExit && activeCarsList.some(c => c.car === carAtExit)) {
        selectedCar = carAtExit;
      } else if (activeCarsList.length > 0 && !selectedCar) {
        selectedCar = activeCarsList[0].car;
      }

      updateActiveButton();
      if (selectedCar) {
        loadCarOrderData(selectedCar);
      } else {
        renderNoActiveCars();
      }
    } catch (e) {
      console.error('Error fetching active cars:', e);
      renderFallbackGrid();
    }
  }

  function renderCarSelector(cars, carAtExit) {
    if (!checkoutCarGrid) return;
    if (activeCountBadge) {
      activeCountBadge.textContent = `${cars.length} Vehicle${cars.length === 1 ? '' : 's'} Inside`;
    }

    if (cars.length === 0) {
      checkoutCarGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 1.5rem; text-align: center; background: #0a0a0a; border: 1px dashed var(--border-medium); border-radius: 6px; color: var(--text-muted); font-size: 0.85rem;">
          No vehicles currently inside facility. All cars 1-8 are outside.
        </div>
      `;
      return;
    }

    checkoutCarGrid.innerHTML = cars.map(c => {
      const isExit = c.car === carAtExit;
      const tag = isExit ? ' • AT EXIT' : (c.slot ? ` • ${c.slot}` : ' • In Deck');
      return `
        <button class="car-select-btn ${c.car === selectedCar ? 'active' : ''} ${isExit ? 'at-exit' : ''}" 
                data-car="${c.car}" 
                style="${isExit ? 'border-color: #f59e0b; box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);' : ''}">
          Car #${c.car}${tag}
        </button>
      `;
    }).join('');

    // Attach click handlers
    checkoutCarGrid.querySelectorAll('.car-select-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const cId = parseInt(btn.getAttribute('data-car'), 10);
        selectedCar = cId;
        updateActiveButton();
        loadCarOrderData(cId);
      });
    });
  }

  function renderFallbackGrid() {
    if (!checkoutCarGrid) return;
    let html = '';
    for (let i = 1; i <= 8; i++) {
      html += `<button class="car-select-btn ${i === 1 ? 'active' : ''}" data-car="${i}">Car #${i}</button>`;
    }
    checkoutCarGrid.innerHTML = html;
    selectedCar = 1;
    loadCarOrderData(1);
  }

  function updateActiveButton() {
    if (!checkoutCarGrid) return;
    checkoutCarGrid.querySelectorAll('.car-select-btn').forEach(btn => {
      const cId = parseInt(btn.getAttribute('data-car'), 10);
      if (cId === selectedCar) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  function renderNoActiveCars() {
    if (statusCarName) statusCarName.textContent = 'No Cars Inside';
    if (statusPill) {
      statusPill.textContent = 'FACILITY EMPTY';
      statusPill.className = 'slot-status-pill vacant';
    }
    if (statusText) statusText.textContent = 'Drive a car to the entry gate to initiate smart parking.';
    if (billSlotLocation) billSlotLocation.textContent = 'None';
    if (billDwellTime) billDwellTime.textContent = '00:00:00';
    if (billTotalAmount) billTotalAmount.textContent = '₹0.00';
    if (qrAmountText) qrAmountText.textContent = '₹0.00';
    if (qrContainer) {
      qrContainer.innerHTML = '<div style="font-size:0.8rem;color:#94a3b8;padding:1.5rem;text-align:center;">No payment pending</div>';
    }
    if (btnRazorpayPay) btnRazorpayPay.disabled = true;
    if (btnVerifyManual) btnVerifyManual.disabled = true;
  }

  // 2. Fetch Razorpay Order & Scannable QR Code for Selected Car
  async function loadCarOrderData(carId) {
    if (!carId) return;
    try {
      if (qrContainer) {
        qrContainer.innerHTML = '<div style="font-size:0.8rem;color:#64748b;padding:1.5rem;text-align:center;">Generating dynamic QR...</div>';
      }

      const res = await fetch('/api/payment/create-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car: carId })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Could not load vehicle session');
      }

      currentOrderData = await res.json();
      carData = currentOrderData;
      renderOrderView(currentOrderData);
    } catch (e) {
      console.warn('Error loading order data:', e.message);
      // Fallback vehicle status fetch
      fetchFallbackVehicle(carId);
    }
  }

  async function fetchFallbackVehicle(carId) {
    try {
      const res = await fetch(`/api/vehicle/${carId}`);
      if (res.ok) {
        const data = await res.json();
        carData = data;
        renderVehicleFallback(data);
      }
    } catch (e) {
      console.error('Fallback error:', e);
    }
  }

  function renderOrderView(order) {
    if (!order) return;

    if (statusCarName) statusCarName.textContent = `Car #${order.car}`;
    if (billBaseFee) billBaseFee.textContent = `₹50.00 (First 3 hrs)`;
    if (billHourlyRate) billHourlyRate.textContent = `+₹20.00 / hr extra`;

    const floorName = order.slot && order.slot.startsWith('F') ? 'First Floor' : 'Ground Floor';
    const bayDesc = order.slot ? `${floorName} (Bay ${order.slot})` : 'Entry Deck Level';

    if (statusPill) {
      statusPill.textContent = order.slot ? `PARKED IN ${order.slot}` : 'IN FACILITY';
      statusPill.className = 'slot-status-pill occupied';
    }
    if (statusText) {
      statusText.textContent = `Ultrasonic occupancy verified • Location: ${bayDesc}.`;
    }
    if (billSlotLocation) billSlotLocation.textContent = bayDesc;

    const fare = order.fare || 50.0;
    if (billTotalAmount) billTotalAmount.textContent = `₹${fare.toFixed(2)}`;
    if (qrAmountText) qrAmountText.textContent = `₹${fare.toFixed(2)}`;
    if (upiIdDisplay) upiIdDisplay.textContent = order.upi_id || 'parktrack360@okaxis';

    // Render real scannable QR Code image
    if (qrContainer && order.qr_code_image) {
      qrContainer.innerHTML = `
        <img src="${order.qr_code_image}" 
             alt="Scannable UPI QR Code" 
             style="width: 100%; height: 100%; object-fit: contain; border-radius: 4px;" />
      `;
    }

    if (btnRazorpayPay) {
      btnRazorpayPay.disabled = false;
      btnRazorpayPay.style.opacity = '1';
    }
    if (btnVerifyManual) {
      btnVerifyManual.disabled = false;
      btnVerifyManual.style.opacity = '1';
    }

    startDwellTicker(order.dwell_s || 0);
  }

  function renderVehicleFallback(v) {
    if (statusCarName) statusCarName.textContent = `Car #${v.car}`;
    if (billTotalAmount) billTotalAmount.textContent = `₹${(v.current_fare || 50).toFixed(2)}`;
    if (qrAmountText) qrAmountText.textContent = `₹${(v.current_fare || 50).toFixed(2)}`;
    startDwellTicker(v.dwell_s || 0);
  }

  function startDwellTicker(initialSec) {
    if (dwellTimerInterval) clearInterval(dwellTimerInterval);
    let s = initialSec;
    if (billDwellTime) billDwellTime.textContent = formatDuration(s);

    dwellTimerInterval = setInterval(() => {
      s++;
      if (billDwellTime) billDwellTime.textContent = formatDuration(s);
    }, 1000);
  }

  function formatDuration(sec) {
    const s = Math.floor(sec || 0);
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // 2.5 PhonePe Payment Flow & Automatic Status Polling
  let phonePePollTimer = null;

  async function openPhonePeCheckout() {
    if (!selectedCar) {
      alert('Please select an active vehicle inside the facility.');
      return;
    }

    if (btnPhonePePay) {
      btnPhonePePay.disabled = true;
      btnPhonePePay.innerHTML = `<span>Connecting to PhonePe...</span>`;
    }

    try {
      const res = await fetch('/api/payment/phonepe/create-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car: selectedCar })
      });

      const data = await res.json();
      if (!data.ok || !data.payment_url) {
        throw new Error(data.detail || data.error || 'Failed to initiate PhonePe order');
      }

      console.log('PhonePe Order Initiated:', data);

      // Open PhonePe checkout in a new window/tab
      const payWindow = window.open(data.payment_url, '_blank');

      if (btnPhonePePay) {
        btnPhonePePay.innerHTML = `<span>Awaiting Payment • Auto-opening Gate...</span>`;
      }

      // Start automatic polling every 2 seconds
      if (phonePePollTimer) clearInterval(phonePePollTimer);
      const pollCar = selectedCar;
      const txnId = data.txn_id;

      phonePePollTimer = setInterval(async () => {
        try {
          const pollRes = await fetch(`/api/payment/phonepe/status/${pollCar}/${txnId}`);
          const pollData = await pollRes.json();
          console.log('PhonePe Poll Status:', pollData);

          if (pollData.ok && pollData.is_paid) {
            clearInterval(phonePePollTimer);
            if (payWindow && !payWindow.closed) {
              payWindow.close();
            }
            showReceipt({
              receipt_id: `PHON-${pollCar}-${Date.now().toString().slice(-6)}`,
              car: pollCar,
              fare: pollData.fare || currentOrderData?.fare || 50.0
            }, 'PhonePe UPI');
          }
        } catch (pollErr) {
          console.warn('Poll error:', pollErr);
        }
      }, 2000);

      // Stop polling after 4 minutes timeout
      setTimeout(() => {
        if (phonePePollTimer) {
          clearInterval(phonePePollTimer);
          if (btnPhonePePay) {
            btnPhonePePay.disabled = false;
            btnPhonePePay.innerHTML = `<span>Pay with PhonePe / UPI (Instant)</span>`;
          }
        }
      }, 240000);

    } catch (e) {
      console.error('PhonePe initiation error:', e);
      alert(`Could not start PhonePe checkout: ${e.message}`);
      if (btnPhonePePay) {
        btnPhonePePay.disabled = false;
        btnPhonePePay.innerHTML = `<span>Pay with PhonePe / UPI (Instant)</span>`;
      }
    }
  }

  // 3. Razorpay Checkout Modal
  function openRazorpayCheckout() {
    if (!currentOrderData || !selectedCar) {
      alert('Please select an active vehicle inside the facility.');
      return;
    }

    const keyId = currentOrderData.razorpay_key_id || 'rzp_test_parktrack360';
    const amountPaise = Math.round((currentOrderData.fare || 50.0) * 100);

    const options = {
      key: keyId,
      amount: amountPaise,
      currency: "INR",
      name: "ParkTrack 360",
      description: `Parking Clearance for Car #${selectedCar}`,
      order_id: currentOrderData.order_id && !currentOrderData.order_id.startsWith("order_sim") ? currentOrderData.order_id : undefined,
      handler: function (response) {
        console.log("Razorpay payment response:", response);
        verifyAndOpenGate({
          car: selectedCar,
          razorpay_order_id: response.razorpay_order_id || currentOrderData.order_id,
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_signature: response.razorpay_signature,
          method: "Razorpay Checkout"
        });
      },
      prefill: {
        name: `Driver of Car #${selectedCar}`,
        contact: "9876543210",
        email: `car${selectedCar}@parktrack360.local`
      },
      theme: {
        color: "#f59e0b"
      },
      modal: {
        ondismiss: function () {
          console.log("Razorpay checkout modal dismissed by user.");
        }
      }
    };

    try {
      if (typeof Razorpay !== 'undefined') {
        const rzp = new Razorpay(options);
        rzp.on('payment.failed', function (resp) {
          alert(`Payment failed: ${resp.error.description}`);
        });
        rzp.open();
      } else {
        // Fallback to direct verification
        verifyAndOpenGate({
          car: selectedCar,
          order_id: currentOrderData.order_id,
          method: "Simulated UPI QR"
        });
      }
    } catch (e) {
      console.warn("Razorpay SDK initialization fallback:", e);
      verifyAndOpenGate({
        car: selectedCar,
        order_id: currentOrderData.order_id,
        method: "UPI QR Scan"
      });
    }
  }

  // 4. Verify Payment & Open Exit Barrier Gate
  async function verifyAndOpenGate(payload) {
    if (btnRazorpayPay) btnRazorpayPay.disabled = true;
    if (btnVerifyManual) btnVerifyManual.disabled = true;

    try {
      const res = await fetch('/api/payment/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (data.ok) {
        showReceipt(data, payload.method || 'Razorpay UPI');
      } else {
        alert(`Payment verification failed: ${data.detail || data.reason || 'Could not verify'}`);
        if (btnRazorpayPay) btnRazorpayPay.disabled = false;
        if (btnVerifyManual) btnVerifyManual.disabled = false;
      }
    } catch (e) {
      console.error('Verification error:', e);
      alert('Error connecting to settlement server.');
      if (btnRazorpayPay) btnRazorpayPay.disabled = false;
      if (btnVerifyManual) btnVerifyManual.disabled = false;
    }
  }

  function showReceipt(data, method) {
    if (dwellTimerInterval) clearInterval(dwellTimerInterval);
    if (checkoutView) checkoutView.style.display = 'none';
    if (receiptView) receiptView.style.display = 'block';

    if (receiptIdText) receiptIdText.textContent = `Receipt #${data.receipt_id}`;
    if (rcpCarNum) rcpCarNum.textContent = `Car #${data.car}`;
    if (rcpSlotId) rcpSlotId.textContent = carData?.slot ? `Bay ${carData.slot}` : 'Assigned Bay';
    if (rcpDuration) rcpDuration.textContent = formatDuration(carData?.dwell_s || 0);
    if (rcpMethod) rcpMethod.textContent = method;
    if (rcpAmountPaid) rcpAmountPaid.textContent = `₹${(data.fare || 50.0).toFixed(2)}`;

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Event Listeners
  if (btnPhonePePay) {
    btnPhonePePay.addEventListener('click', openPhonePeCheckout);
  }

  if (btnRazorpayPay) {
    btnRazorpayPay.addEventListener('click', openRazorpayCheckout);
  }

  if (btnVerifyManual) {
    btnVerifyManual.addEventListener('click', () => {
      if (!selectedCar) {
        alert('Please select an active vehicle.');
        return;
      }
      verifyAndOpenGate({
        car: selectedCar,
        method: "Scanned UPI QR Code"
      });
    });
  }

  // WebSocket for Live State Synchronization
  function connectLiveSync() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/ui`;
    try {
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const snap = JSON.parse(event.data);
          if (snap.t === 'snapshot') {
            // If car at exit changed, re-render
            loadActiveCars();
          }
        } catch (e) {}
      };
      ws.onclose = () => {
        setTimeout(connectLiveSync, 3000);
      };
    } catch (e) {}
  }

  // Initialization
  loadActiveCars();
  connectLiveSync();

})();
