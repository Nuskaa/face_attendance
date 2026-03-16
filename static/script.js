/**
 * AI Face Recognition Attendance System
 * script.js — Frontend Logic
 */

"use strict";

// ─── State ────────────────────────────────────────────────────────────────────
let cameraRunning = false;     // is the webcam stream active?
let attendanceData = [];       // cached attendance records
let allRecords = [];           // unfiltered copy for search/filter

// ─── On Page Load ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  startClock();
  refreshStudents();
  refreshAttendance();

  // Poll attendance every 5 seconds for live camera updates
  setInterval(refreshAttendance, 5000);
});

// ═══════════════════════════════════════════════════════════════════════════════
//  CLOCK
// ═══════════════════════════════════════════════════════════════════════════════
function startClock() {
  function tick() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    document.getElementById('live-clock').textContent = `${h}:${m}:${s}`;

    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const day = String(now.getDate()).padStart(2,'0');
    const mon = months[now.getMonth()];
    const yr  = now.getFullYear();
    document.getElementById('live-date').textContent = `${day} ${mon} ${yr}`;
  }
  tick();
  setInterval(tick, 1000);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  STUDENTS
// ═══════════════════════════════════════════════════════════════════════════════
async function refreshStudents() {
  try {
    const res  = await fetch('/api/students');
    const data = await res.json();
    document.getElementById('stat-total-label').textContent = data.count;
  } catch (e) {
    console.error('Failed to load students:', e);
  }
}

async function reloadFaces() {
  const btn = document.querySelector('.reload-btn');
  btn.classList.add('spinning');
  try {
    const res  = await fetch('/api/reload_faces', { method: 'POST' });
    const data = await res.json();
    showToast('success', 'Faces Reloaded', `${data.students.length} student(s) loaded.`);
    refreshStudents();
  } catch (e) {
    showToast('error', 'Reload Failed', 'Could not reload faces.');
  } finally {
    btn.classList.remove('spinning');
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  ATTENDANCE TABLE
// ═══════════════════════════════════════════════════════════════════════════════
async function refreshAttendance() {
  try {
    const res  = await fetch('/api/attendance');
    const data = await res.json();

    attendanceData = data.records;
    allRecords     = [...attendanceData];

    document.getElementById('stat-today-label').textContent = data.today_count;
    document.getElementById('record-count').textContent = `${data.total} record${data.total !== 1 ? 's' : ''}`;

    buildDateFilter(attendanceData);
    renderTable(attendanceData);
    updateRosterFromAttendance(attendanceData);
  } catch (e) {
    console.error('Failed to refresh attendance:', e);
  }
}

function buildDateFilter(records) {
  const sel   = document.getElementById('filter-date');
  const current = sel.value;
  const dates = [...new Set(records.map(r => r.Date))].sort().reverse();

  // Re-populate but keep selection if it still exists
  sel.innerHTML = '<option value="">All Dates</option>';
  dates.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    if (d === current) opt.selected = true;
    sel.appendChild(opt);
  });
}

function renderTable(records, flashNames = []) {
  const tbody = document.getElementById('attendance-tbody');

  if (!records || records.length === 0) {
    tbody.innerHTML = `
      <tr class="empty-row">
        <td colspan="4">
          <span class="bi bi-inbox"></span>
          No records yet
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => {
    const isNew = flashNames.includes(r.Name);
    return `
      <tr class="${isNew ? 'row-new' : ''}">
        <td>${escHtml(r.Name)}</td>
        <td>${escHtml(r.Time)}</td>
        <td>${escHtml(r.Date)}</td>
        <td>
          <span class="status-badge present">
            <span class="bi bi-check-circle-fill"></span>
            ${escHtml(r.Status)}
          </span>
        </td>
      </tr>`;
  }).join('');
}

function filterTable() {
  const query    = document.getElementById('search-input').value.toLowerCase().trim();
  const dateVal  = document.getElementById('filter-date').value;

  let filtered = allRecords;

  if (query)   filtered = filtered.filter(r => r.Name.toLowerCase().includes(query));
  if (dateVal) filtered = filtered.filter(r => r.Date === dateVal);

  renderTable(filtered);
}

function updateRosterFromAttendance(records) {
  const today = new Date();
  const d = String(today.getDate()).padStart(2,'0');
  const m = String(today.getMonth()+1).padStart(2,'0');
  const y = today.getFullYear();
  const todayStr = `${d}-${m}-${y}`;

  const presentToday = new Set(
    records.filter(r => r.Date === todayStr).map(r => r.Name.toLowerCase())
  );

  document.querySelectorAll('.roster-item').forEach(item => {
    const name = item.id.replace('roster-', '');
    const isPresent = presentToday.has(name);

    const dot    = document.getElementById(`dot-${name}`);
    const status = document.getElementById(`status-${name}`);

    item.classList.toggle('present', isPresent);
    if (dot) {
      dot.classList.toggle('present', isPresent);
      dot.classList.toggle('absent', !isPresent);
    }
    if (status) {
      status.textContent = isPresent ? 'Present ✓' : 'Absent';
      status.className = `roster-status ${isPresent ? 'present' : 'absent'}`;
    }
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  UPLOAD PHOTO
// ═══════════════════════════════════════════════════════════════════════════════
async function handleUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Switch viewport to loading state
  showViewportLoading('Analysing image…');
  setRecIndicator('processing', 'PROCESSING');

  const formData = new FormData();
  formData.append('image', file);

  try {
    const res  = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (!data.success) {
      showToast('error', 'Upload Failed', data.error || 'Unknown error.');
      resetViewport();
      setRecIndicator('', 'IDLE');
      return;
    }

    // Show annotated image
    hideViewportLoading();
    showResultImage(data.annotated_image);
    setRecIndicator('success', 'DONE');

    // Notifications per recognised face
    const newNames = [];
    data.results.forEach(r => {
      if (r.name !== 'Unknown') {
        const msg = r.is_new ? 'Marked Present for today' : 'Already marked today';
        showToast('success', `✓ ${r.name}`, msg);
        if (r.is_new) newNames.push(r.name);
      } else {
        showToast('warning', 'Unknown Face', 'Face detected but not recognised.');
      }
    });

    if (data.faces_detected === 0) {
      showToast('info', 'No Faces Found', 'No faces detected in the uploaded image.');
    }

    // Summary toast
    if (data.faces_detected > 0) {
      showToast(
        'info',
        'Recognition Complete',
        `${data.recognized} / ${data.faces_detected} face(s) recognised.`
      );
    }

    // Refresh table with highlights
    await refreshAttendance();
    if (newNames.length > 0) {
      renderTable(allRecords.slice(0, 50), newNames);
    }

  } catch (e) {
    console.error(e);
    showToast('error', 'Network Error', 'Could not reach the server.');
    resetViewport();
    setRecIndicator('', 'IDLE');
  }

  // Reset the file input so the same file can be re-uploaded
  event.target.value = '';
}

// ═══════════════════════════════════════════════════════════════════════════════
//  CAMERA
// ═══════════════════════════════════════════════════════════════════════════════
async function toggleCamera() {
  if (cameraRunning) {
    await stopCamera();
  } else {
    await startCamera();
  }
}

async function startCamera() {
  try {
    const res  = await fetch('/api/camera/start', { method: 'POST' });
    const data = await res.json();
    if (!data.success) { showToast('error', 'Camera Error', data.message); return; }

    cameraRunning = true;
    updateCameraBtn(true);

    // Show feed, hide idle
    document.getElementById('viewport-idle').classList.add('hidden');
    document.getElementById('upload-result-img').classList.add('hidden');
    document.getElementById('camera-feed-wrap').classList.remove('hidden');

    // Force reload of the MJPEG stream
    const feed = document.getElementById('camera-feed');
    feed.src = '/video_feed?' + Date.now();

    setRecIndicator('live', 'LIVE');
    showToast('info', 'Camera Started', 'Live face recognition is now active.');

  } catch (e) {
    showToast('error', 'Camera Error', 'Could not start the camera.');
  }
}

async function stopCamera() {
  try {
    await fetch('/api/camera/stop', { method: 'POST' });
  } catch (e) { /* best effort */ }

  cameraRunning = false;
  updateCameraBtn(false);

  document.getElementById('camera-feed-wrap').classList.add('hidden');
  document.getElementById('viewport-idle').classList.remove('hidden');

  setRecIndicator('', 'IDLE');
  showToast('info', 'Camera Stopped', 'Webcam has been released.');
  await refreshAttendance();
}

function updateCameraBtn(active) {
  const btn = document.getElementById('btn-camera');
  btn.classList.toggle('active', active);
  btn.innerHTML = active
    ? '<span class="bi bi-stop-circle"></span><span>Stop Camera</span>'
    : '<span class="bi bi-camera-video"></span><span>Start Camera</span>';
}

// ═══════════════════════════════════════════════════════════════════════════════
//  RESET ATTENDANCE
// ═══════════════════════════════════════════════════════════════════════════════
function confirmReset() {
  document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}

async function doReset() {
  closeModal();
  try {
    const res  = await fetch('/api/reset_attendance', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('success', 'Attendance Reset', 'All records have been cleared.');
      await refreshAttendance();
    }
  } catch (e) {
    showToast('error', 'Error', 'Could not reset attendance.');
  }
}

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', function (e) {
  if (e.target === this) closeModal();
});

// ═══════════════════════════════════════════════════════════════════════════════
//  VIEWPORT HELPERS
// ═══════════════════════════════════════════════════════════════════════════════
function showViewportLoading(msg = 'Processing…') {
  // Remove any existing loader
  document.querySelectorAll('.loading-overlay').forEach(el => el.remove());

  const wrap = document.getElementById('viewport-wrap');
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.innerHTML = `
    <div class="spinner"></div>
    <p>${msg}</p>`;
  wrap.appendChild(overlay);
}

function hideViewportLoading() {
  document.querySelectorAll('.loading-overlay').forEach(el => el.remove());
}

function showResultImage(src) {
  const img = document.getElementById('upload-result-img');
  document.getElementById('viewport-idle').classList.add('hidden');
  document.getElementById('camera-feed-wrap').classList.add('hidden');
  img.src = src;
  img.classList.remove('hidden');
}

function resetViewport() {
  hideViewportLoading();
  document.getElementById('upload-result-img').classList.add('hidden');
  document.getElementById('camera-feed-wrap').classList.add('hidden');
  document.getElementById('viewport-idle').classList.remove('hidden');
}

function setRecIndicator(type, label) {
  const el = document.getElementById('rec-indicator');
  el.className = `rec-indicator ${type}`;
  document.getElementById('rec-label').textContent = label;
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════════════════════
const TOAST_ICONS = {
  success: 'bi-check-circle-fill',
  error:   'bi-x-circle-fill',
  info:    'bi-info-circle-fill',
  warning: 'bi-exclamation-triangle-fill',
};

function showToast(type, title, message, duration = 4000) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon bi ${TOAST_ICONS[type] || 'bi-bell'}"></span>
    <div class="toast-body">
      <div class="toast-title">${escHtml(title)}</div>
      ${message ? `<div class="toast-msg">${escHtml(message)}</div>` : ''}
    </div>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('hiding');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }, duration);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  UTILITIES
// ═══════════════════════════════════════════════════════════════════════════════
function escHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
