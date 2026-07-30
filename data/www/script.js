// Add or modify masterspools here
// Format: { id, label, weight (in grams), image (URL or path) }
const masterspools = [
    {
        id: 'bambu_grey',
        label: 'BambuLab Grey',
        weight: 210,
        image: 'img/bambu_grey.png'
    },
    {
        id: 'bambu_transp',
        label: 'BambuLab Transparent',
        weight: 215,
        image: 'img/bambu_transp.png'
    },
    {
        id: 'r3d_grey',
        label: 'R3D Grey',
        weight: 239,
        image: 'img/r3d_grey.png'
    },
    {
        id: 'custom',
        label: 'Custom',
        weight: 0,
        image: 'img/custom.png'
    }
];

// ========== I18N HOOK ==========
// Translations are handled by i18n.js + locales/*.json (9 languages).
// window.t() and window.setLanguage() are provided by i18n.js as compat shims.
// We hook in only for data-tooltip sync and updateCloudText() refresh.
document.addEventListener('i18n:applied', () => {
    // Sync CSS ::after tooltips (i18n.js sets title + aria-label; we also need data-tooltip)
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        el.setAttribute('data-tooltip', el.title || el.getAttribute('aria-label') || '');
    });
    updateCloudText();
});

// ========== DOM ELEMENTS ==========
const cloudDot = document.getElementById('cloudDot');
const cloudText = document.getElementById('cloudText');
const fbDot = document.getElementById('fbDot');
const fbText = document.getElementById('fbText');
const dbDot  = document.getElementById('dbDot');
const dbText = document.getElementById('dbText');
const weightEl = document.getElementById('weight');
const uidEl = document.getElementById('uid');
const calFactorEl = document.getElementById('calFactor');
const sendStateEl = document.getElementById('sendState');
const userNameEl = document.getElementById('userName');

// ========== STATE ==========
let currentWeight = null;
let currentUid = null;
let calFactor = null;
let cloudStatus = 'unknown';
let firebaseConfigured = false;

// UID state — kept in sync from WS / snapshot
let _uidLeft  = '';   // physically scanned (rfid2, left reader)
let _uidRight = '';   // physically scanned (rfid1, right reader)
let _uidTwin  = '';   // fetched from Firestore when one physical slot is empty

// Uptime live counter — resync from firmware, advance locally every second
let _uptimeBase   = null;  // uptime_s received from firmware
let _uptimeBaseAt = null;  // Date.now() when it was received
let _uptimeTicker = null;  // setInterval handle

function _startUptimeTicker() {
    if (_uptimeTicker) return;
    _uptimeTicker = setInterval(() => {
        if (_uptimeBase === null) return;
        const elapsed = (Date.now() - _uptimeBaseAt) / 1000;
        const upEl = document.getElementById('uptime');
        if (upEl) upEl.textContent = formatHMS(_uptimeBase + elapsed);
    }, 1000);
}

function _syncUptime(secs) {
    _uptimeBase   = secs;
    _uptimeBaseAt = Date.now();
    const upEl = document.getElementById('uptime');
    if (upEl) upEl.textContent = formatHMS(secs);
    _startUptimeTicker();
}

// ========== UTILITIES ==========
function setTextIfChanged(el, txt) {
    if (!el || el.textContent === txt) return;
    el.textContent = txt;
}

function toggleSection(el) {
    el.classList.toggle('active');
    const content = el.nextElementSibling;
    content.classList.toggle('active');
}

function updateCloudText() {
    const txt = cloudStatus === 'up' || cloudStatus === 'ok' ? t('cloud') : t('offline');
    setTextIfChanged(cloudText, txt);
}

function setCloudStatus(state) {
    // Accept both legacy string ("ok"/"down") and new boolean true/false
    cloudStatus = (state === true || state === 'up' || state === 'ok') ? 'up' : 'down';
    const ok = cloudStatus === 'up';
    const info = document.getElementById('cloudInfo');
    if (info) info.style.display = ok ? 'none' : '';
    if (!ok) {
        updateCloudText();
        if (cloudDot) cloudDot.className = 'status-dot error';
    }
}

function setDbStatus(s) {
    if (!dbDot || !dbText) return;
    const info = document.getElementById('dbInfo');
    if (s.db_updating) {
        if (info) info.style.display = '';
        dbDot.className = 'status-dot warning';
        setTextIfChanged(dbText, 'DB ↻');
        return;
    }
    // WS sends db_ok (bool); /api/status sends db_brands + db_materials (counts)
    const loaded = (typeof s.db_ok !== 'undefined')
        ? !!s.db_ok
        : (s.db_brands > 0 && s.db_materials > 0);
    if (!loaded) {
        if (info) info.style.display = '';
        dbDot.className = 'status-dot error';
        setTextIfChanged(dbText, 'DB !');
        return;
    }
    // DB is healthy — hide the indicator
    if (info) info.style.display = 'none';
}

function setFirebaseConfigured(flag) {
    firebaseConfigured = !!flag;
    const el = document.getElementById('firebaseStatus');
    if (el) setTextIfChanged(el, firebaseConfigured ? t('validated') : t('notConfigured'));
    const fbInfo = document.getElementById('fbInfo');
    if (firebaseConfigured) {
        if (fbInfo) fbInfo.style.display = 'none';
    } else {
        if (fbInfo) fbInfo.style.display = '';
        if (fbDot)  fbDot.className = 'status-dot warning';
        if (fbText) setTextIfChanged(fbText, 'FB OFF');
    }
    // Toggle the Account card (visible only when authenticated)
    const accountCard = document.getElementById('accountCard');
    if (accountCard) accountCard.style.display = firebaseConfigured ? '' : 'none';
    // Auto-show/hide login modal — only after we know the actual status (not on init)
    if (typeof firebaseStatusKnown !== 'undefined' && firebaseStatusKnown) {
        if (firebaseConfigured) hideAuthModal(); else showAuthModal();
    }
}

// Update the Account card with the user's displayName/email + avatar initials.
// Called from applyStatusSnapshot when /api/status or WS reports firebase info.
function _getInitials(displayName, email) {
    if (displayName && displayName.trim()) {
        const words = displayName.trim().split(/\s+/).filter(w => w.length > 0);
        if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
        return words[0][0].toUpperCase();
    }
    return email ? email.charAt(0).toUpperCase() : '?';
}

function setAccountInfo(email, displayName) {
    if (!email && !displayName) return;
    const emailEl  = document.getElementById('accountEmail');
    const nameEl   = document.getElementById('accountName');
    const avatarEl = document.getElementById('accountAvatar');

    if (emailEl) setTextIfChanged(emailEl, email || '');

    if (nameEl) {
        if (displayName && displayName.trim()) {
            setTextIfChanged(nameEl, displayName.trim());
            nameEl.style.display = '';
        } else {
            nameEl.style.display = 'none';
        }
    }

    if (avatarEl) avatarEl.textContent = _getInitials(displayName, email);

    // Show displayName (or email fallback) in the weight card header
    if (userNameEl) {
        const label = (displayName && displayName.length) ? displayName : (email || '');
        if (label) {
            setTextIfChanged(userNameEl, label);
            userNameEl.classList.remove('hidden');
        }
    }
}

function setSendState(msg, color) {
    if (!msg) {
        sendStateEl.classList.add('hidden');
        return;
    }
    setTextIfChanged(sendStateEl, msg);
    if (color) sendStateEl.style.background = color;
    sendStateEl.classList.remove('hidden');
}

function formatHMS(secs) {
    if (!isFinite(secs)) return '--:--:--';
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    return [h,m,s].map(x => String(x).padStart(2,'0')).join(':');
}

// ========== API FUNCTIONS ==========
function updateFirebaseAuth() {
    const emailEl = document.getElementById('firebaseEmail');
    const passEl = document.getElementById('firebasePassword');
    const email = (emailEl?.value || '').trim();
    const password = (passEl?.value || '').trim();
    if (!email || !password) {
        alert(t('alertFirebaseError'));
        return;
    }
    fetch('/api/firebase/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(res => {
        setFirebaseConfigured(!!res.configured);
        alert(t('alertFirebaseSaved'));
    })
    .catch(() => alert(t('alertFirebaseError')));
}

function deleteFirebaseAuth() {
    fetch('/api/firebase/logout', { method: 'POST' })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(() => {
        const emailEl = document.getElementById('firebaseEmail');
        const passEl = document.getElementById('firebasePassword');
        if (emailEl) emailEl.value = '';
        if (passEl) passEl.value = '';
        setFirebaseConfigured(false);
        alert(t('alertFirebaseDeleted'));
    })
    .catch(() => alert(t('alertFirebaseError')));
}

// ========== API KEY VISIBILITY TOGGLE ==========
function tareScale() {
    fetch('/api/tare', { method: 'POST' })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .catch(() => {});
}

// ========== TARE HOLD BUTTON ==========
let tareTimer = null;
let tareBtn = null;

function startTare() {
    if (!tareBtn) tareBtn = document.getElementById('tareBtn');
    
    // Add holding class to start animation
    tareBtn.classList.add('holding');
    
    // Set timer for 1 second
    tareTimer = setTimeout(() => {
        // Execute tare after 1 second
        tareScale();
        
        // Visual feedback
        tareBtn.classList.remove('holding');
        tareBtn.classList.add('success');
        
        // Reset after short delay
        setTimeout(() => {
            tareBtn.classList.remove('success');
            const progress = tareBtn.querySelector('.tare-progress');
            if (progress) progress.style.width = '0';
        }, 500);
    }, 1000);
}

function cancelTare() {
    if (!tareBtn) tareBtn = document.getElementById('tareBtn');
    
    // Cancel timer
    if (tareTimer) {
        clearTimeout(tareTimer);
        tareTimer = null;
    }
    
    // Remove holding class
    tareBtn.classList.remove('holding');
    
    // Reset progress bar
    const progress = tareBtn.querySelector('.tare-progress');
    if (progress) {
        progress.style.width = '0';
    }
}

// ========== TARE BUTTON IN CALIBRATION WIZARD ==========
let tareBtnCalib = null;
let tareTimerCalib = null;

function startTareCalib() {
    if (!tareBtnCalib) tareBtnCalib = document.getElementById('tareBtnCalib');
    
    // Add holding class to start animation
    tareBtnCalib.classList.add('holding');
    
    // Set timer for 1 second
    tareTimerCalib = setTimeout(() => {
        // Execute tare after 1 second
        tareScale();
        
        // Visual feedback
        tareBtnCalib.classList.remove('holding');
        tareBtnCalib.classList.add('success');
        
        // Reset after short delay
        setTimeout(() => {
            tareBtnCalib.classList.remove('success');
            const progress = tareBtnCalib.querySelector('.tare-progress');
            if (progress) progress.style.width = '0';
        }, 500);
    }, 1000);
}

function cancelTareCalib() {
    if (!tareBtnCalib) tareBtnCalib = document.getElementById('tareBtnCalib');
    
    // Cancel timer
    if (tareTimerCalib) {
        clearTimeout(tareTimerCalib);
        tareTimerCalib = null;
    }
    
    // Remove holding class
    tareBtnCalib.classList.remove('holding');
    
    // Reset progress bar
    const progress = tareBtnCalib.querySelector('.tare-progress');
    if (progress) {
        progress.style.width = '0';
    }
}

function updateCalibration() {
    const factor = parseFloat(document.getElementById('newCalFactor').value);
    if (isNaN(factor)) { 
        alert(t('alertInvalidFactor'));
        return;
    }
    
    // Validation: factor must be positive
    if (factor <= 0) {
        alert(t('alertNegativeFactor'));
        return;
    }
    
    fetch('/api/calibration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: factor })
    })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .catch(() => alert(t('alertError')));
}

function computeFactor() {
    const known = parseFloat(document.getElementById('knownWeight').value);
    if (isNaN(known) || known <= 0) {
        alert(t('alertInvalidWeight'));
        return;
    }
    if (currentWeight === null || calFactor === null) {
        alert(t('alertDataUnavailable'));
        return;
    }
    
    const newFactor = calFactor * (currentWeight / known);
    document.getElementById('newCalFactor').value = newFactor.toFixed(3);
    
    fetch('/api/calibration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: newFactor })
    })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .catch(() => alert(t('alertError')));
}

function resetWiFi() {
    if (!confirm(t('alertReconfigConfirm'))) return;
    fetch('/api/reset-wifi', { method: 'POST' })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .catch(() => {});
}

function factoryReset() {
    if (!confirm(t('alertResetConfirm'))) return;
    fetch('/api/factory-reset', { method: 'POST' })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .catch(() => {});
}

// ========== CALIBRATION WIZARD ==========
function populateMasterspoolSelect() {
    const select = document.getElementById('masterspoolSelect');
    if (!select) return;
    
    // Clear existing options
    select.innerHTML = '';
    
    // Add masterspools as options
    masterspools.forEach(spool => {
        const option = document.createElement('option');
        option.value = spool.id;
        option.textContent = spool.label;
        select.appendChild(option);
    });
    
    // Trigger change to show first image
    onMasterspoolChange();
}

function onMasterspoolChange() {
    const select = document.getElementById('masterspoolSelect');
    const customInput = document.getElementById('calibKnownWeight');
    const img = document.getElementById('masterspoolImg');
    const errorMsg = document.getElementById('calibWeightError');
    
    if (!select) return;
    
    const selectedId = select.value;
    const selectedSpool = masterspools.find(s => s.id === selectedId);
    
    if (!selectedSpool) return;
    
    // Clear any previous error
    if (customInput) customInput.classList.remove('error');
    if (errorMsg) errorMsg.style.display = 'none';
    
    // Show/hide custom input
    if (selectedId === 'custom') {
        customInput.style.display = 'block';
        customInput.value = '';
        customInput.focus();
        
        // Add input listener to clear error on typing
        customInput.oninput = function() {
            if (this.classList.contains('error')) {
                this.classList.remove('error');
                if (errorMsg) errorMsg.style.display = 'none';
            }
        };
    } else {
        customInput.style.display = 'none';
        customInput.value = selectedSpool.weight;
    }
    
    // Update main image
    if (selectedSpool.image && img) {
        img.src = selectedSpool.image;
        img.style.display = 'block';
        img.onerror = function() {
            // If image fails to load, hide it
            this.style.display = 'none';
        };
    }
}

function updateProgressDots(activeStep) {
    document.querySelectorAll('.progress-dots .dot').forEach((dot, index) => {
        const step = index + 1;
        dot.classList.remove('active', 'completed');
        
        if (step === activeStep) {
            dot.classList.add('active');
        } else if (step < activeStep) {
            dot.classList.add('completed');
        }
    });
}

function calibStep1() {
    // Tare the scale
    fetch('/api/tare', { method: 'POST' })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(() => {
        // Move to step 2
        document.getElementById('step1').classList.remove('active');
        document.getElementById('step2').classList.add('active');
        updateProgressDots(2);
        
        // Initialize masterspool selector (set default value)
        populateMasterspoolSelect();
    })
    .catch(() => alert(t('alertError')));
}

function calibStep2() {
    const knownWeight = parseFloat(document.getElementById('calibKnownWeight').value);
    
    // Validation 1: if user entered weight is invalid or <= 0
    if (isNaN(knownWeight) || knownWeight <= 0) {
        showWeightInvalidModal();
        return;
    }
    
    // Validation 2: if user entered weight is between 0 and 200g
    if (knownWeight < 200) {
        showWeightErrorModal();
        return;
    }
    
    // Check data availability
    if (currentWeight === null || calFactor === null) {
        alert(t('alertDataUnavailable'));
        return;
    }
    
    // Calculate new factor
    const newFactor = calFactor * (currentWeight / knownWeight);
    
    // Validation: factor must be positive
    if (newFactor <= 0) {
        alert(t('alertNegativeFactor'));
        return;
    }
    
    // Send to device
    fetch('/api/calibration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: newFactor })
    })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(() => {
        // Move to step 3
        document.getElementById('step2').classList.remove('active');
        document.getElementById('step3').classList.add('active');
        updateProgressDots(3);
    })
    .catch(() => alert(t('alertError')));
}

function calibBack(step) {
    // Go back to step
    document.getElementById('step2').classList.remove('active');
    document.getElementById('step' + step).classList.add('active');
    updateProgressDots(step);
    
    // Clear input
    document.getElementById('calibKnownWeight').value = '';
}

function calibReset() {
    // Reset wizard to step 1
    document.getElementById('step3').classList.remove('active');
    document.getElementById('step1').classList.add('active');
    updateProgressDots(1);
    
    // Clear input
    document.getElementById('calibKnownWeight').value = '';
}

// ========== WEIGHT ERROR MODAL ==========
function showWeightErrorModal() {
    const modal = document.getElementById('weightErrorModal');
    if (modal) {
        modal.classList.add('show');
    }
}

function closeWeightErrorModal() {
    const modal = document.getElementById('weightErrorModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

function showWeightInvalidModal() {
    const modal = document.getElementById('weightInvalidModal');
    if (modal) {
        modal.classList.add('show');
    }
}

function closeWeightInvalidModal() {
    const modal = document.getElementById('weightInvalidModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Close modal on click outside
document.addEventListener('DOMContentLoaded', function() {
    const errorModal = document.getElementById('weightErrorModal');
    const invalidModal = document.getElementById('weightInvalidModal');
    
    if (errorModal) {
        errorModal.addEventListener('click', function(e) {
            if (e.target === errorModal) {
                closeWeightErrorModal();
            }
        });
    }
    
    if (invalidModal) {
        invalidModal.addEventListener('click', function(e) {
            if (e.target === invalidModal) {
                closeWeightInvalidModal();
            }
        });
    }
});

// ========== STATUS MANAGEMENT ==========
function applyStatusSnapshot(s) {
    if (!s || typeof s !== 'object') return;
    
    // Raw weight — big number (always shown) + kept for calibration
    if (typeof s.weight !== 'undefined') {
        currentWeight = s.weight;
        setTextIfChanged(weightEl, String(s.weight));
    }

    // Spool / Filament row — always visible, shows — when no value available
    if (typeof s.containerWeight !== 'undefined') {
        const cwEl = document.getElementById('containerWeightDisplay');
        const nwEl = document.getElementById('netWeightDisplay');
        if (cwEl) setTextIfChanged(cwEl, s.containerWeight > 0 ? String(s.containerWeight) : '—');
        if (nwEl) setTextIfChanged(nwEl, (s.containerWeight > 0 && typeof s.netWeight !== 'undefined' && s.netWeight >= 0)
                                          ? String(s.netWeight) : '—');
    }

    // UID state — update tracked values then refresh display
    let uidChanged = false;
    if (typeof s.uid_left  !== 'undefined') { _uidLeft  = s.uid_left  || ''; uidChanged = true; }
    if (typeof s.uid_right !== 'undefined') { _uidRight = s.uid_right || ''; uidChanged = true; currentUid = _uidRight; }
    if (typeof s.uid       !== 'undefined' && typeof s.uid_right === 'undefined') {
        // fallback for older firmware frames
        _uidRight = s.uid || ''; uidChanged = true; currentUid = _uidRight;
    }
    if (typeof s.uid_twin  !== 'undefined') { _uidTwin  = s.uid_twin  || ''; uidChanged = true; }
    if (uidChanged) _refreshUidDisplays();

    // Show/hide UID rows based on hardware config
    _updateUidRows();

    // Filament info panel (brand / material / color from RFID scan)
    if (typeof s.brand !== 'undefined' || typeof s.material !== 'undefined' || typeof s.color !== 'undefined') {
        _updateFilamentPanel(s);
    }

    // Cloud
    if (typeof s.cloud !== 'undefined') {
        setCloudStatus(s.cloud);
    }

    // DB status (WS sends db_ok bool; /api/status sends db_brands/db_materials counts)
    if (typeof s.db_ok !== 'undefined' || typeof s.db_brands !== 'undefined') {
        setDbStatus(s);
    }
    
    // API UI removed in Firebase-only mode
    // Modal trigger uses firebaseAuth ("am I signed in right now?") rather than
    // firebaseConfigured ("are creds stored?") — this catches the stale-creds case
    // (e.g. password changed on Firebase side) where stored creds exist but sign-in
    // fails on boot, in which case we want the user to re-authenticate via the modal.
    if (typeof s.firebaseAuth !== 'undefined') {
        firebaseStatusKnown = true; // status is real now, modal can react
        setFirebaseConfigured(!!s.firebaseAuth);
    } else if (typeof s.firebaseConfigured !== 'undefined') {
        firebaseStatusKnown = true;
        setFirebaseConfigured(!!s.firebaseConfigured);
    }
    if (typeof s.firebaseEmail === 'string' || typeof s.firebaseDisplayName === 'string') {
        // Keep the (now hidden) input updated for backward-compat callers
        const emailEl = document.getElementById('firebaseEmail');
        if (emailEl && s.firebaseEmail && !emailEl.value) emailEl.value = s.firebaseEmail;
        // Feed Account card + userName label in weight card
        setAccountInfo(s.firebaseEmail || '', s.firebaseDisplayName || '');
    }
    
    // Calibration factor
    if (typeof s.calibrationFactor !== 'undefined') {
        const n = Number(s.calibrationFactor);
        const shown = isFinite(n) ? n.toFixed(2) : '—';
        setTextIfChanged(calFactorEl, shown);
        calFactor = n;
    }
    
    // Uptime — sync anchor from firmware, local ticker advances between frames
    if (typeof s.uptime_s !== 'undefined' || typeof s.uptime_ms !== 'undefined') {
        const secs = (typeof s.uptime_s !== 'undefined') ? Number(s.uptime_s) : Number(s.uptime_ms) / 1000;
        _syncUptime(secs);
    }

    // Firmware version
    if (typeof s.fw_version === 'string' && s.fw_version) {
        const fwEl = document.getElementById('fwVersion');
        if (fwEl) setTextIfChanged(fwEl, 'v' + s.fw_version);
    }

    // Workflow state badge (top-left overlay on the weight card)
    if (typeof s.scaleStatus !== 'undefined') {
        const v = String(s.scaleStatus || '').trim();
        if (v === 'idle') {
            setSendState(t('placeASpool'),  'rgba(72,187,120,0.35)');
        } else if (v.startsWith('scanning:')) {
            setSendState(t('scanningRfid'), 'rgba(100,160,255,0.30)');
        } else if (v.startsWith('stable:')) {
            setSendState(t('stabilizing'),  'rgba(255,200,80,0.30)');
        } else if (v === 'send') {
            setSendState(t('sending'),      'rgba(255,255,255,0.22)');
        } else if (v === 'success') {
            setSendState(t('sent'),         'rgba(72,187,120,0.40)');
        } else if (v === 'error') {
            setSendState(t('sendError'),    'rgba(245,101,101,0.40)');
        } else if (v === 'done') {
            setSendState(t('removeSpool'),  'rgba(255,160,50,0.35)');
        } else if (v === 'ready') {
            setSendState(t('readyForSpool'),'rgba(72,187,120,0.35)');
            _clearFilamentPanel();
        } else if (/^\d+$/.test(v)) {
            setSendState(t('sendIn') + ' ' + v + 's', 'rgba(255,255,255,0.22)');
        }
    }
}

function pollStatus() {
    fetch('/api/status', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(s => applyStatusSnapshot(s))
    .catch(() => {});
}

// ========== AUTH MODAL ==========
// Tracks whether we have received a real firebaseConfigured status from /api/status
// Prevents the modal from flashing on first load (before we know the actual state)
let firebaseStatusKnown = false;

// Bridge page URL (Firebase Hosting target "cdn" → site "tigertag-cdn")
const AUTH_BRIDGE_URL = 'https://tigertag-cdn.web.app/scale-auth.html';
const AUTH_BRIDGE_ORIGIN = 'https://tigertag-cdn.web.app';

let _authPopup = null;
let _authPopupWatcher = null;

function showAuthModal() {
    const m = document.getElementById('firebaseLoginModal');
    if (!m) return;
    m.style.display = 'flex';
    m.setAttribute('aria-hidden', 'false');
}
function hideAuthModal() {
    const m = document.getElementById('firebaseLoginModal');
    if (!m) return;
    m.style.display = 'none';
    m.setAttribute('aria-hidden', 'true');
    setAuthError('');
}
function setAuthError(msg, isSuccess = false) {
    const el = document.getElementById('authError');
    if (!el) return;
    if (!msg) { el.style.display = 'none'; el.textContent = ''; return; }
    el.textContent = msg;
    el.style.display = 'block';
    el.style.background = isSuccess ? '#eafaf1' : '#fdeaea';
    el.style.color       = isSuccess ? '#1e8449' : '#c0392b';
}

function forgotPassword() {
    const email = (document.getElementById('loginEmail')?.value || '').trim();
    if (!email) { setAuthError(t('authEnterEmailFirst')); return; }
    setAuthError('');
    const FIREBASE_API_KEY = 'AIzaSyCkxPTs_Cv0KVLqsZj-UKWWqIY0OtfVpnw';
    fetch(`https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key=${FIREBASE_API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requestType: 'PASSWORD_RESET', email })
    })
    .then(r => r.json().then(j => ({ ok: r.ok, body: j })))
    .then(({ ok, body }) => {
        if (!ok) {
            const code = body?.error?.message || '';
            setAuthError(t(code === 'EMAIL_NOT_FOUND' ? 'authEmailNotFound' : 'authNetworkError'));
            return;
        }
        setAuthError(t('authResetSent'), true);
    })
    .catch(() => setAuthError(t('authNetworkError')));
}

// ── Auth mode toggle (signin ↔ signup) ──
const FIREBASE_API_KEY = 'AIzaSyCkxPTs_Cv0KVLqsZj-UKWWqIY0OtfVpnw';

function switchAuthMode(mode) {
    setAuthError('');
    const isSignup = mode === 'signup';
    document.querySelectorAll('[data-signup-only]').forEach(el => el.style.display = isSignup ? '' : 'none');
    document.querySelectorAll('[data-signin-only]').forEach(el => el.style.display = isSignup ? 'none' : '');
    const titleEl = document.getElementById('authTitle');
    const subEl   = document.getElementById('authSubText');
    if (titleEl) titleEl.textContent = t(isSignup ? 'authSignUpTitle' : 'authTitle');
    if (subEl)   subEl.textContent   = t(isSignup ? 'authSignUpSub'   : 'authSub');
    const passEl = document.getElementById('loginPassword');
    if (passEl) passEl.setAttribute('autocomplete', isSignup ? 'new-password' : 'current-password');
    // Reset confirm/name fields when switching
    if (!isSignup) {
        const cp = document.getElementById('signupConfirmPassword');
        const dn = document.getElementById('signupDisplayName');
        if (cp) cp.value = '';
        if (dn) dn.value = '';
    }
}

// ── Email / Password sign-up (Firebase REST API → /api/firebase/token) ──
async function signUpWithEmail() {
    const email       = (document.getElementById('loginEmail')?.value || '').trim();
    const password    = (document.getElementById('loginPassword')?.value || '').trim();
    const confirm     = (document.getElementById('signupConfirmPassword')?.value || '').trim();
    const displayName = (document.getElementById('signupDisplayName')?.value || '').trim();

    if (!email || !password) { setAuthError(t('alertError')); return; }
    if (password !== confirm) { setAuthError(t('authPasswordMismatch')); return; }
    if (password.length < 6)  { setAuthError(t('authWeakPassword')); return; }

    setAuthError('');

    try {
        // 1. Create account
        const r = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${FIREBASE_API_KEY}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, returnSecureToken: true })
        });
        const data = await r.json();
        if (!r.ok) {
            const code = data?.error?.message || '';
            if (code === 'EMAIL_EXISTS')        { setAuthError(t('authEmailInUse'));     return; }
            if (code.startsWith('WEAK_PASSWORD')){ setAuthError(t('authWeakPassword')); return; }
            setAuthError(t('alertError'));
            return;
        }

        // 2. Set display name if provided
        if (displayName) {
            await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:update?key=${FIREBASE_API_KEY}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ idToken: data.idToken, displayName, returnSecureToken: false })
            }).catch(() => {});
        }

        // 3. Store tokens on device
        const tr = await fetch('/api/firebase/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                idToken:      data.idToken,
                refreshToken: data.refreshToken,
                uid:          data.localId,
                email:        data.email || email,
                displayName:  displayName,
                provider:     'password'
            })
        });
        if (!tr.ok) throw new Error('token store failed');

        setFirebaseConfigured(true);
        hideAuthModal();

    } catch (_) {
        setAuthError(t('authNetworkError'));
    }
}

// ── Email / Password sign-in (uses existing /api/firebase/auth endpoint) ──
function signInWithEmail() {
    setAuthError('');
    const email = (document.getElementById('loginEmail')?.value || '').trim();
    const password = (document.getElementById('loginPassword')?.value || '').trim();
    if (!email || !password) {
        setAuthError(t('alertError'));
        return;
    }
    fetch('/api/firebase/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    })
    .then(r => r.json().then(j => ({ ok: r.ok, status: r.status, body: j })))
    .then(({ ok, status, body }) => {
        if (!ok || !body.auth) {
            setAuthError(t(status === 401 ? 'authInvalidCreds' : 'alertFirebaseError'));
            return;
        }
        setFirebaseConfigured(true);
        hideAuthModal();
    })
    .catch(() => setAuthError(t('authNetworkError')));
}

// ── Google sign-in via OAuth bridge (popup → postMessage) ──
function signInWithGoogleBridge() {
    setAuthError('');

    // The bridge needs to know our origin to validate + postMessage back to us
    const returnTo = encodeURIComponent(location.origin);
    const url = `${AUTH_BRIDGE_URL}?return_to=${returnTo}`;

    // Open centered popup
    const w = 460, h = 640;
    const left = Math.max(0, (screen.width - w) / 2);
    const top = Math.max(0, (screen.height - h) / 2);
    _authPopup = window.open(
        url,
        'tigertag-auth',
        `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );

    if (!_authPopup) {
        setAuthError(t('authPopupBlocked'));
        return;
    }

    // Watch for popup closed without success
    if (_authPopupWatcher) clearInterval(_authPopupWatcher);
    _authPopupWatcher = setInterval(() => {
        if (_authPopup && _authPopup.closed) {
            clearInterval(_authPopupWatcher);
            _authPopupWatcher = null;
            _authPopup = null;
        }
    }, 500);
}

// ── Sign out — clears tokens on the device and re-opens the login modal ──
function signOut() {
    if (!confirm(t('confirmSignOut'))) return;
    fetch('/api/firebase/logout', { method: 'POST' })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(() => {
        // Reset local UI state
        const emailEl = document.getElementById('firebaseEmail');
        const passEl = document.getElementById('firebasePassword');
        if (emailEl) emailEl.value = '';
        if (passEl) passEl.value = '';
        // Clear the modal's input fields too (so the next user starts fresh)
        const loginEmail = document.getElementById('loginEmail');
        const loginPass = document.getElementById('loginPassword');
        if (loginEmail) loginEmail.value = '';
        if (loginPass) loginPass.value = '';
        setAccountInfo('', '');
        if (userNameEl) { userNameEl.textContent = ''; userNameEl.classList.add('hidden'); }
        const avatarEl = document.getElementById('accountAvatar');
        if (avatarEl) avatarEl.textContent = '?';
        setFirebaseConfigured(false); // this also re-shows the modal via setFirebaseConfigured
    })
    .catch(() => alert(t('alertFirebaseError')));
}

// ── postMessage listener — receives tokens from the bridge ──
window.addEventListener('message', (event) => {
    // SECURITY: only accept messages from the bridge origin
    if (event.origin !== AUTH_BRIDGE_ORIGIN) return;
    const data = event.data;
    if (!data || data.type !== 'tigertag-auth' || !data.payload) return;

    const p = data.payload;
    if (!p.idToken || !p.refreshToken || !p.uid) {
        setAuthError(t('alertFirebaseError'));
        return;
    }

    // Send tokens to the firmware
    fetch('/api/firebase/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            idToken: p.idToken,
            refreshToken: p.refreshToken,
            uid: p.uid,
            email: p.email || '',
            displayName: p.displayName || '',
            provider: p.provider || 'google.com'
        })
    })
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(() => {
        setFirebaseConfigured(true);
        hideAuthModal();
        // Best-effort close of the popup
        try { if (_authPopup) _authPopup.close(); } catch {}
    })
    .catch(() => setAuthError(t('authNetworkError')));
});

// ========== WEBSOCKET CLIENT ==========
let _ws = null;
let _wsReconnectTimer = null;

let _pollTimer = null;
let _wsConnected = false;
let _wsFailed = false;

function pollStatus() {
    fetch('/api/status', { cache: 'no-cache' })
    .then(r => r.json())
    .then(data => { applyStatusSnapshot(data); })
    .catch(() => {});
}

function startPolling() {
    if (_pollTimer) return;
    console.log('[POLL] Starting HTTP polling (no WebSocket)');
    pollStatus();
    _pollTimer = setInterval(pollStatus, 1000);
}

function stopPolling() {
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

function wsConnect() {
    if (_ws && (_ws.readyState === WebSocket.OPEN || _ws.readyState === WebSocket.CONNECTING)) return;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    _ws = new WebSocket(proto + '//' + location.host + '/ws');

    let wsOpenTimer = setTimeout(function() {
        if (!_wsConnected && !_wsFailed) {
            _wsFailed = true;
            console.log('[WS] connection timeout — falling back to polling');
            startPolling();
        }
    }, 5000);

    _ws.onopen = function() {
        console.log('[WS] connected');
        _wsConnected = true;
        clearTimeout(wsOpenTimer);
        stopPolling();
        if (_wsReconnectTimer) { clearTimeout(_wsReconnectTimer); _wsReconnectTimer = null; }
    };

    _ws.onmessage = function(evt) {
        wsLogPush('in', evt.data);
        try {
            const data = JSON.parse(evt.data);
            if (data.type === 'firebaseStatus') {
                firebaseStatusKnown = true;
                setFirebaseConfigured(!!(data.auth || data.configured));
                if (data.email || data.displayName) setAccountInfo(data.email || '', data.displayName || '');
                return;
            }
            applyStatusSnapshot(data);
        } catch(e) {}
    };

    const _origSend = _ws.send.bind(_ws);
    _ws.send = function(data) { wsLogPush('out', data); _origSend(data); };

    _ws.onerror = function() {
        clearTimeout(wsOpenTimer);
        if (!_wsFailed) { _wsFailed = true; startPolling(); }
    };

    _ws.onclose = function() {
        console.log('[WS] closed');
        _wsConnected = false;
        clearTimeout(wsOpenTimer);
        if (!_pollTimer) startPolling();
        if (!_wsReconnectTimer) {
            _wsReconnectTimer = setTimeout(function() {
                _wsReconnectTimer = null;
                _wsFailed = false;
                wsConnect();
            }, 10000);
        }
    };
}

// ========== HARDWARE CONFIG ==========
let hwConfig = { rfidCount: 1, rfidSide: 'left', motorConnected: false, motorEnabled: false, motorSpeed: 3 };

async function fetchHardwareConfig() {
    try {
        const r = await fetch('/api/hw/config', { cache: 'no-cache' });
        if (!r.ok) return;
        const d = await r.json();
        hwConfig = { ...hwConfig, ...d };
    } catch (_) {}
    applyHardwareConfig();
}

function applyHardwareConfig() {
    // RFID count segment
    document.querySelectorAll('#rfidSegment .segment-btn').forEach(b => {
        b.classList.toggle('active', +b.dataset.val === hwConfig.rfidCount);
    });
    // RFID side selector — visible only when count=1
    const sideRow = document.getElementById('rfidSideRow');
    if (sideRow) sideRow.style.display = (hwConfig.rfidCount === 1) ? '' : 'none';
    // RFID side segment
    const side = hwConfig.rfidSide || 'left';
    document.querySelectorAll('#rfidSideSegment .segment-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.val === side);
    });
    // Motor connected toggle
    const connChk = document.getElementById('motorConnectedCheck');
    if (connChk) connChk.checked = !!hwConfig.motorConnected;
    const enabledRow = document.getElementById('motorEnabledRow');
    if (enabledRow) enabledRow.style.display = hwConfig.motorConnected ? '' : 'none';
    const enChk = document.getElementById('motorEnabledCheck');
    if (enChk) enChk.checked = !!hwConfig.motorEnabled;
    // Motor speed — init slider + noise badge without triggering a save
    const spd = hwConfig.motorSpeed || 3;
    _motorTestSpeed = spd;
    const slider = document.getElementById('motorSpeedSlider');
    if (slider) slider.value = spd;
    _updateMotorNoiseBadge(spd);
    updateMotorTestPanel();
    updateRfidTestPanel();
    _updateUidRows();
}

async function saveHardwareConfig() {
    try {
        await fetch('/api/hw/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(hwConfig)
        });
    } catch (_) {}
}

function setRfidCount(n) {
    hwConfig.rfidCount = n;
    document.querySelectorAll('#rfidSegment .segment-btn').forEach(b => {
        b.classList.toggle('active', +b.dataset.val === n);
    });
    const sideRow = document.getElementById('rfidSideRow');
    if (sideRow) sideRow.style.display = (n === 1) ? '' : 'none';
    updateRfidTestPanel();
    saveHardwareConfig();
}

function setRfidSide(side) {
    hwConfig.rfidSide = side;
    document.querySelectorAll('#rfidSideSegment .segment-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.val === side);
    });
    updateRfidTestPanel();
    saveHardwareConfig();
}

function onMotorConnectedChange() {
    const chk = document.getElementById('motorConnectedCheck');
    hwConfig.motorConnected = !!(chk && chk.checked);
    const row = document.getElementById('motorEnabledRow');
    if (row) row.style.display = hwConfig.motorConnected ? '' : 'none';
    if (!hwConfig.motorConnected) {
        hwConfig.motorEnabled = false;
        const enChk = document.getElementById('motorEnabledCheck');
        if (enChk) enChk.checked = false;
        stopMotorTest();
    }
    updateMotorTestPanel();
    saveHardwareConfig();
}

function onMotorEnabledChange() {
    const chk = document.getElementById('motorEnabledCheck');
    hwConfig.motorEnabled = !!(chk && chk.checked);
    if (!hwConfig.motorEnabled) stopMotorTest();
    updateMotorTestPanel();
    fetch('/api/servo-toggle', { method: 'POST' })
        .then(r => r.ok ? r.json() : Promise.reject())
        .catch(() => {
            hwConfig.motorEnabled = !hwConfig.motorEnabled;
            const c = document.getElementById('motorEnabledCheck');
            if (c) c.checked = hwConfig.motorEnabled;
        });
    saveHardwareConfig();
}

// ── Motor test ──────────────────────────────────────────────────────────────
const MOTOR_SPEED_US = { 1: 1530, 2: 1580, 3: 1650, 4: 1750, 5: 1900 };
let _motorTestRunning = false;
let _motorTestSpeed   = 2;

function updateMotorTestPanel() {
    const panel = document.getElementById('motorTestPanel');
    if (!panel) return;
    const show = !!(hwConfig.motorConnected && hwConfig.motorEnabled);
    panel.style.display = show ? '' : 'none';
    if (!show && _motorTestRunning) stopMotorTest();
    _updateMotorTestBtn();
}

function _updateMotorNoiseBadge(level) {
    const badge = document.getElementById('motorNoiseBadge');
    const label = document.getElementById('motorNoiseLabel');
    let noiseKey, icon;
    if (level <= 2)       { noiseKey = 'motorNoiseQuiet';    icon = '🔇'; }
    else if (level === 3) { noiseKey = 'motorNoiseModerate'; icon = '🔉'; }
    else                  { noiseKey = 'motorNoiseLoud';     icon = '🔊'; }
    if (badge) badge.textContent = icon;
    if (label) { label.textContent = t(noiseKey); label.dataset.i18n = noiseKey; }
}

function setMotorSpeed(level) {
    _motorTestSpeed = level;
    hwConfig.motorSpeed = level;
    const slider = document.getElementById('motorSpeedSlider');
    if (slider) { slider.value = level; slider.style.setProperty('--val', level); }
    document.querySelectorAll('.motor-speed-ticks span').forEach((s, i) => {
        s.style.color = (i + 1 === level) ? '#e67e22' : '';
        s.style.setProperty('--dot', (i + 1 <= level) ? '#e67e22' : '#e2e8f0');
    });
    _updateMotorNoiseBadge(level);
    if (_motorTestRunning) {
        fetch('/api/servo/test', { method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ us: MOTOR_SPEED_US[level] }) }).catch(() => {});
    }
    saveHardwareConfig();
}

function toggleMotorTest() { if (_motorTestRunning) stopMotorTest(); else startMotorTest(); }

function startMotorTest() {
    const us = MOTOR_SPEED_US[_motorTestSpeed] || 1650;
    fetch('/api/servo/test', { method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ us }) })
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(() => { _motorTestRunning = true; _updateMotorTestBtn(); })
    .catch(() => {});
}

function stopMotorTest() {
    fetch('/api/servo/test', { method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stop: true }) }).catch(() => {});
    _motorTestRunning = false;
    _updateMotorTestBtn();
}

function _updateMotorTestBtn() {
    const btn   = document.getElementById('motorTestRunBtn');
    const label = document.getElementById('motorTestLabel');
    const icon  = document.getElementById('motorTestIcon');
    if (!btn) return;
    btn.classList.toggle('running', _motorTestRunning);
    if (label) label.textContent = _motorTestRunning ? t('motorTestStop') : t('motorTestRun');
    if (icon) icon.innerHTML = _motorTestRunning
        ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>'
        : '<polygon points="5,3 19,12 5,21"/>';
}

// ── RFID hardware test ───────────────────────────────────────────────────────
let _rfidTestRunning = false;
let _rfidTestPollId  = null;

function toggleRfidTest() { if (_rfidTestRunning) stopRfidTest(); else startRfidTest(); }

function startRfidTest() {
    _setRfidUid('left',  '—', false);
    _setRfidUid('right', '—', false);
    fetch('/api/rfid/test', { method: 'POST',
        headers: { 'Content-Type': 'application/json' }, body: '{}' })
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(() => {
        _rfidTestRunning = true;
        _updateRfidTestBtn();
        _rfidTestPollId = setInterval(_pollRfidTestUid, 600);
    })
    .catch(() => {});
}

function stopRfidTest() {
    clearInterval(_rfidTestPollId); _rfidTestPollId = null;
    fetch('/api/rfid/test', { method: 'POST',
        headers: { 'Content-Type': 'application/json' }, body: '{"stop":true}' }).catch(() => {});
    _rfidTestRunning = false;
    _updateRfidTestBtn();
}

function _pollRfidTestUid() {
    fetch('/api/rfid/test')
        .then(r => r.ok ? r.json() : Promise.reject())
        .then(d => {
            if (d.uid_left)  _setRfidUid('left',  d.uid_left,  true);
            if (d.uid_right) _setRfidUid('right', d.uid_right, true);
        })
        .catch(() => {});
}

function _setRfidUid(side, text, detected) {
    const el  = document.getElementById(side === 'left' ? 'rfidTestUidLeft'  : 'rfidTestUidRight');
    const btn = document.getElementById(side === 'left' ? 'rfidClearBtnLeft' : 'rfidClearBtnRight');
    if (!el) return;
    el.textContent = text;
    el.classList.toggle('uid-detected', !!detected);
    if (btn) btn.style.display = detected ? '' : 'none';
}

function clearRfidUid(side) {
    fetch('/api/rfid/test', { method: 'POST',
        headers: { 'Content-Type': 'application/json' }, body: '{"reset":true}' }).catch(() => {});
    _setRfidUid(side, '—', false);
}

function _updateRfidTestBtn() {
    const btn   = document.getElementById('rfidTestRunBtn');
    const label = document.getElementById('rfidTestLabel');
    const icon  = document.getElementById('rfidTestIcon');
    if (!btn) return;
    btn.classList.toggle('running', _rfidTestRunning);
    if (label) label.textContent = _rfidTestRunning ? t('motorTestStop') : t('rfidTestScan');
    if (icon) icon.innerHTML = _rfidTestRunning
        ? '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>'
        : '<polygon points="5,3 19,12 5,21"/>';
}

function updateRfidTestPanel() {
    if (_rfidTestRunning && !hwConfig.rfidCount) stopRfidTest();
    const leftRow  = document.getElementById('rfidLeftRow');
    const rightRow = document.getElementById('rfidRightRow');
    if (hwConfig.rfidCount >= 2) {
        if (leftRow)  leftRow.style.display = '';
        if (rightRow) rightRow.style.display = '';
    } else {
        const activeSide = hwConfig.rfidSide || 'left';
        if (leftRow)  leftRow.style.display  = (activeSide === 'left')  ? '' : 'none';
        if (rightRow) rightRow.style.display = (activeSide === 'right') ? '' : 'none';
    }
}

function updateSpoolStatus(detected, position) {
    const detEl  = document.getElementById('spoolDetectedVal');
    const posRow = document.getElementById('spoolPositionRow');
    const posEl  = document.getElementById('spoolPositionVal');
    if (!detEl) return;
    if (detected) {
        setTextIfChanged(detEl, t('yes'));
        if (posRow) posRow.style.display = '';
        if (posEl && position != null) setTextIfChanged(posEl, String(position));
    } else {
        setTextIfChanged(detEl, t('no'));
        if (posRow) posRow.style.display = 'none';
    }
}

// ========== LOG SIDE PANEL ==========
let _fbLogPollId  = null;
let _logPanelOpen = false;
let _logActiveTab = 'fb';

function logPanelOpen(tab) {
    _logPanelOpen = true;
    document.getElementById('logSidePanel').classList.add('open');
    logTabSwitch(tab || _logActiveTab);
}

function logPanelClose() {
    _logPanelOpen = false;
    document.getElementById('logSidePanel').classList.remove('open');
    clearInterval(_fbLogPollId); _fbLogPollId = null;
}

function logTabSwitch(tab) {
    _logActiveTab = tab;
    document.getElementById('logPaneFb').classList.toggle('active', tab === 'fb');
    document.getElementById('logPaneWs').classList.toggle('active', tab === 'ws');
    document.getElementById('logTabFb').classList.toggle('active', tab === 'fb');
    document.getElementById('logTabWs').classList.toggle('active', tab === 'ws');
    if (tab === 'fb') {
        fbLogFetch();
        if (!_fbLogPollId) _fbLogPollId = setInterval(fbLogFetch, 4000);
    } else {
        clearInterval(_fbLogPollId); _fbLogPollId = null;
    }
}

// ========== FIREBASE LOG ==========

async function fbLogFetch() {
    const btn = document.getElementById('fbLogRefreshBtn');
    if (btn) btn.textContent = '…';
    try {
        const r = await fetch('/api/logs', { cache: 'no-store' });
        if (!r.ok) throw new Error(r.status);
        const entries = await r.json();   // array of strings, oldest first
        _fbLogRender(entries);
    } catch (_) {
        const c = document.getElementById('fbLogContainer');
        if (c) c.innerHTML = '<div class="ws-log-empty" style="color:#fc8181">Erreur de connexion</div>';
    } finally {
        if (btn) btn.textContent = '↺';
    }
}

function _fbLogEntryClass(line) {
    if (/ERR|FAIL|error|INVALID/i.test(line)) return 'fb-log-err';
    if (/ OK\b|result=|Signed|signed|AUTH OK/i.test(line)) return 'fb-log-ok';
    if (/TOKEN|REFRESH|auth/i.test(line)) return 'fb-log-auth';
    if (/PATCH|CONTAINER|TWIN|WEIGHT/i.test(line)) return 'fb-log-data';
    return '';
}

function _fbLogRender(entries) {
    const container = document.getElementById('fbLogContainer');
    const countEl   = document.getElementById('fbLogCount');
    if (!container) return;
    if (countEl) countEl.textContent = entries.length;
    if (entries.length === 0) {
        container.innerHTML = '<div class="ws-log-empty">Aucun log Firebase</div>';
        return;
    }
    // Show newest first
    container.innerHTML = entries.slice().reverse().map(line => {
        const cls = _fbLogEntryClass(line);
        return `<div class="fb-log-entry ${cls}"><pre class="ws-log-data">${line}</pre></div>`;
    }).join('');
}

async function fbLogClear() {
    try {
        await fetch('/api/logs/clear', { method: 'POST' });
        _fbLogRender([]);
    } catch (_) {}
}

async function fbLogCopy() {
    const container = document.getElementById('fbLogContainer');
    const btn = document.getElementById('fbLogCopyBtn');
    if (!container) return;
    const lines = Array.from(container.querySelectorAll('pre.ws-log-data'))
        .map(el => el.textContent)
        .reverse()   // restore chronological order (oldest first)
        .join('\n');
    try {
        await navigator.clipboard.writeText(lines || '(empty)');
        if (btn) { const t = btn.textContent; btn.textContent = '✓'; setTimeout(() => btn.textContent = t, 1500); }
    } catch (_) {}
}

// ========== WEBSOCKET LOG ==========
const WS_LOG_MAX = 100;
let _wsLogEntries    = [];
let _wsLogPaused     = false;
let _wsLogOnlyChange = true;
let _wsLogLastRaw    = null;
let _wsLogRenderTimer = null;

// ========== FILAMENT PANEL ==========
// Tracked values (so partial WS deltas can update only the changed field)
let _fpBrand    = '';
let _fpMaterial = '';
let _fpColor    = '';  // raw string from firmware e.g. "Red #FF0000"

function _clearFilamentPanel() {
    _fpBrand = ''; _fpMaterial = ''; _fpColor = '';
    const panel = document.getElementById('filamentPanel');
    if (panel) panel.style.display = 'none';
}

function _updateFilamentPanel(s) {
    if (typeof s.brand    !== 'undefined') _fpBrand    = s.brand    || '';
    if (typeof s.material !== 'undefined') _fpMaterial = s.material || '';
    if (typeof s.color    !== 'undefined') _fpColor    = s.color    || '';

    const panel  = document.getElementById('filamentPanel');
    const dotEl  = document.getElementById('filamentColorDot');
    const brandEl = document.getElementById('filamentBrand');
    const matEl   = document.getElementById('filamentMaterial');
    if (!panel) return;

    // Treat "--" (firmware sentinel for "no data") as empty
    const brand = (_fpBrand    === '--') ? '' : _fpBrand;
    const mat   = (_fpMaterial === '--') ? '' : _fpMaterial;
    const col   = (_fpColor    === '--') ? '' : _fpColor;

    const hasInfo = brand.length > 0 || mat.length > 0;
    panel.style.display = hasInfo ? '' : 'none';
    if (!hasInfo) return;

    if (brandEl) setTextIfChanged(brandEl, brand || '—');
    if (matEl)   setTextIfChanged(matEl,   mat   || '—');
    if (dotEl) {
        // Extract "#RRGGBB" from the color string (e.g. "Red #FF0000")
        let hex = col.match(/#[0-9A-Fa-f]{6}/)?.[0];
        // Fallback: map known color name words to hex
        if (!hex && col) {
            const NAME_MAP = {
                white:'#FFFFFF', branco:'#FFFFFF', blanc:'#FFFFFF', blanco:'#FFFFFF', weiss:'#FFFFFF',
                black:'#000000', preto:'#000000', noir:'#000000', negro:'#000000', schwarz:'#000000',
                gray:'#808080',  grey:'#808080',  cinza:'#808080', gris:'#808080', grau:'#808080',
                red:'#E53935',   vermelho:'#E53935', rouge:'#E53935', rojo:'#E53935', rot:'#E53935',
                blue:'#1E88E5',  azul:'#1E88E5',   bleu:'#1E88E5',  blau:'#1E88E5',
                green:'#43A047', verde:'#43A047',  vert:'#43A047',  grun:'#43A047',
                yellow:'#FDD835',amarelo:'#FDD835', jaune:'#FDD835', amarillo:'#FDD835', gelb:'#FDD835',
                orange:'#FB8C00',laranja:'#FB8C00', orange_fr:'#FB8C00',
                purple:'#8E24AA',roxo:'#8E24AA',   violet:'#8E24AA', lila:'#8E24AA',
                pink:'#F06292',  rosa:'#F06292',   rose:'#F06292',
                cyan:'#00ACC1',  turquoise:'#00ACC1',
                brown:'#6D4C41', castanho:'#6D4C41', marron:'#6D4C41', cafe:'#6D4C41',
            };
            const key = col.toLowerCase().split(/[\s_#]/)[0];
            hex = NAME_MAP[key] || null;
        }
        dotEl.style.background = hex || 'rgba(255,255,255,0.25)';
    }
}

// Refresh what is shown in each UID slot.
// Physical UID → shown as-is.
// Slot empty + other slot has UID → show uid_twin (real UID) if available, else "🔗 Twin" placeholder.
// Both slots empty → show "—".
function _refreshUidDisplays() {
    const leftEl  = document.getElementById('uidLeftDisplay');
    const rightEl = document.getElementById('uid');
    const twinRow = document.getElementById('uidTwinRow');
    if (twinRow) twinRow.style.display = 'none';  // always hidden — folded into left/right slots

    const TWIN_PH = t('uidTwin');  // "🔗 Twin" / "🔗 Jumeau"

    function resolve(physical, otherPhysical) {
        if (physical)                     return { text: physical,  twin: false };
        if (otherPhysical && _uidTwin)    return { text: _uidTwin,  twin: true  };
        if (otherPhysical)                return { text: TWIN_PH,   twin: true  };
        return                                   { text: '—',       twin: false };
    }

    const L = resolve(_uidLeft,  _uidRight);
    const R = resolve(_uidRight, _uidLeft);

    if (leftEl) {
        setTextIfChanged(leftEl, L.text);
        leftEl.classList.toggle('uid-value--twin', L.twin);
    }
    if (rightEl) {
        setTextIfChanged(rightEl, R.text);
        rightEl.classList.toggle('uid-value--twin', R.twin);
    }
}

function _updateUidRows() {
    const leftRow  = document.getElementById('uidLeftRow');
    const rightRow = document.getElementById('uidRightRow');
    if (!leftRow || !rightRow) return;
    if (hwConfig.rfidCount >= 2) {
        leftRow.style.display  = '';
        rightRow.style.display = '';
    } else {
        const side = hwConfig.rfidSide || 'left';
        leftRow.style.display  = (side === 'left')  ? '' : 'none';
        rightRow.style.display = (side === 'right') ? '' : 'none';
    }
}

function wsLogPush(dir, raw) {
    if (_wsLogPaused) return;
    if (_wsLogOnlyChange && dir === 'in' && raw === _wsLogLastRaw) return;
    if (dir === 'in') _wsLogLastRaw = raw;

    const now  = new Date();
    const ts   = now.toTimeString().slice(0, 8) + '.' + String(now.getMilliseconds()).padStart(3, '0');
    let display;
    try {
        // Pretty-print only small payloads, compact otherwise
        const obj = JSON.parse(raw);
        const compact = JSON.stringify(obj);
        display = compact.length < 300 ? compact : JSON.stringify(obj, null, 2);
    } catch (_) { display = raw; }

    _wsLogEntries.unshift({ ts, dir, display });
    if (_wsLogEntries.length > WS_LOG_MAX) _wsLogEntries.pop();

    // Throttle DOM update to ~4 fps
    if (!_wsLogRenderTimer) {
        _wsLogRenderTimer = setTimeout(() => { _wsLogRenderTimer = null; _wsLogRender(); }, 250);
    }
}

function _wsLogRender() {
    const container = document.getElementById('wsLogContainer');
    const countEl   = document.getElementById('wsLogCount');
    if (!container) return;
    if (countEl) countEl.textContent = _wsLogEntries.length;
    if (_wsLogEntries.length === 0) {
        container.innerHTML = '<div class="ws-log-empty">Aucun message</div>';
        return;
    }
    const wasAtTop = container.scrollTop < 40;
    container.innerHTML = _wsLogEntries.map(e => {
        const cls   = e.dir === 'in' ? 'ws-log-in' : 'ws-log-out';
        const arrow = e.dir === 'in' ? '↓' : '↑';
        return `<div class="ws-log-entry ${cls}"><span class="ws-log-ts">${e.ts}</span><span class="ws-log-arrow">${arrow}</span><pre class="ws-log-data">${e.display}</pre></div>`;
    }).join('');
    // Keep scroll at top (newest first)
    if (wasAtTop) container.scrollTop = 0;
}

function wsLogClear() {
    _wsLogEntries = [];
    _wsLogLastRaw = null;
    _wsLogRender();
}

function wsLogTogglePause() {
    _wsLogPaused = !_wsLogPaused;
    const btn = document.getElementById('wsLogPauseBtn');
    if (btn) btn.textContent = _wsLogPaused ? '▶' : '⏸';
}

function wsLogSetOnlyChanges(val) {
    _wsLogOnlyChange = !!val;
}

async function wsLogCopy() {
    const btn = document.getElementById('wsLogCopyBtn');
    // Build plain text: oldest first (entries are stored newest-first)
    const lines = _wsLogEntries.slice().reverse().map(e => {
        const dir = e.dir === 'in' ? '↓' : '↑';
        return `${e.ts} ${dir}  ${e.display}`;
    }).join('\n');
    try {
        await navigator.clipboard.writeText(lines || '(empty)');
        if (btn) { const t = btn.textContent; btn.textContent = '✓'; setTimeout(() => btn.textContent = t, 1500); }
    } catch (_) {}
}

// ========== TOOLBOX TOGGLE ==========
function toggleToolbox() {
    const panel = document.getElementById('toolbox');
    const btn   = document.getElementById('toolboxToggle');
    if (!panel) return;
    const isOpen = !panel.classList.contains('collapsed');
    panel.classList.toggle('collapsed', isOpen);
    btn.classList.toggle('open', !isOpen);
    try { localStorage.setItem('tigerscale_toolbox', isOpen ? '0' : '1'); } catch (_) {}
}

function _restoreToolbox() {
    try {
        const saved = localStorage.getItem('tigerscale_toolbox');
        if (saved === '0') {
            const panel = document.getElementById('toolbox');
            const btn   = document.getElementById('toolboxToggle');
            if (panel) panel.classList.add('collapsed');
            if (btn)   btn.classList.remove('open');
        }
    } catch (_) {}
}

// ========== INITIALIZATION ==========
window.onload = () => {
    // Language is applied by i18n.js on DOMContentLoaded — no call needed here
    setFirebaseConfigured(false);
    _restoreToolbox();

    // Initial weight display
    setTextIfChanged(weightEl, '…');

    // Load hardware config from ESP32 (RFID count, motor state)
    fetchHardwareConfig();

    // WebSocket — single data flow, all fields, 250ms same tick as OLED.
    // No HTTP polling: every field (weight, uid, cloud, firebase, calibration,
    // uptime) arrives through the unified WS frame.
    wsConnect();

    // Register Service Worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed'));
    }
};
