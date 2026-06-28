'use strict';

// ---------------------------------------------------------------------------
// Client-side state — mirrors the shape returned by GET /api/status
// ---------------------------------------------------------------------------
const state = {
  animation:   'solid',
  power:       true,
  audioActive: false,
  speedMode:   'manual',
  bpm:         0,
  paramSchema: {},
  params: {
    speed:      0.5,
    brightness: 0.7,
    color:      [255, 140, 0],
  },
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const powerBtn       = document.getElementById('power-btn');
const audioIndicator = document.getElementById('audio-indicator');
const animGrid       = document.getElementById('anim-grid');
const colorSection   = document.getElementById('color-section');
const colorPicker    = document.getElementById('color-picker');
const colorHex       = document.getElementById('color-hex');
const brightnessEl   = document.getElementById('brightness');
const brightnessVal  = document.getElementById('brightness-val');
const speedEl          = document.getElementById('speed');
const speedVal         = document.getElementById('speed-val');
const speedHeading     = document.getElementById('speed-heading');
const speedMinLabel    = document.getElementById('speed-min-label');
const speedMaxLabel    = document.getElementById('speed-max-label');
const speedModeToggle  = document.getElementById('speed-mode-toggle');
const speedSliderRow   = document.getElementById('speed-slider-row');
const bpmRow           = document.getElementById('bpm-row');
const bpmDisplay           = document.getElementById('bpm-display');
const customControlsCard   = document.getElementById('custom-controls-card');
const customControls       = document.getElementById('custom-controls');
const appEl                = document.querySelector('.app');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
}

function hexToRgb(hex) {
  const m = hex.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [255, 255, 255];
}

/** Convert slider integer (0-100) to API float (0.0-1.0). */
const toFloat = v => Math.round(v) / 100;

/** Convert API float (0.0-1.0) to slider integer (0-100). */
const toPct   = v => Math.round(v * 100);

function debounce(fn, ms) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

async function post(url, body) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error(url, res.status, err.error || '');
    }
    return res.ok;
  } catch (e) {
    console.error(url, e);
    return false;
  }
}

// ---------------------------------------------------------------------------
// UI sync — accepts the full /api/status shape or any partial subset
// ---------------------------------------------------------------------------
function applyState(s) {
  if ('animation'    in s) state.animation   = s.animation;
  if ('power'        in s) state.power       = s.power;
  if ('audio_active' in s) state.audioActive = s.audio_active;
  if ('speed_mode'   in s) state.speedMode   = s.speed_mode;
  if ('bpm'          in s) state.bpm         = s.bpm;

  // Merge nested params if present
  if (s.params) {
    if ('speed'      in s.params) state.params.speed      = s.params.speed;
    if ('brightness' in s.params) state.params.brightness = s.params.brightness;
    if ('color'      in s.params) state.params.color      = s.params.color;
    // Custom params
    for (const key of Object.keys(state.paramSchema)) {
      if (key in s.params) state.params[key] = s.params[key];
    }
  }

  // Custom controls — re-render if schema changed, otherwise just sync values
  if ('param_schema' in s) {
    const newKeys = JSON.stringify(Object.keys(s.param_schema).sort());
    const curKeys = JSON.stringify(Object.keys(state.paramSchema).sort());
    state.paramSchema = s.param_schema;
    if (newKeys !== curKeys) {
      renderCustomControls();
    } else {
      syncCustomSliders();
    }
  } else if (s.params) {
    syncCustomSliders();
  }

  // Power button + app dim
  powerBtn.classList.toggle('on',  state.power);
  powerBtn.classList.toggle('off', !state.power);
  appEl.classList.toggle('power-off', !state.power);

  // Audio indicator
  audioIndicator.classList.toggle('active', state.audioActive);

  // Animation grid
  animGrid.querySelectorAll('.anim-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.name === state.animation);
  });

  // Color section: hide for animations that don't use a fixed color.
  // beat_pulse is audio-reactive but does use color, so it's excluded from the hide.
  const hideColor = (AUDIO_REACTIVE.has(state.animation) && state.animation !== 'beat_pulse')
                    || state.animation === 'rainbow';
  colorSection.style.display = hideColor ? 'none' : '';

  // Speed card: toggle only available for solid (manual testing); BPM display always on otherwise
  const isSolid = state.animation === 'solid';
  speedModeToggle.style.display = isSolid ? '' : 'none';
  document.getElementById('speed-mode-manual').classList.toggle('active', state.speedMode === 'manual');
  document.getElementById('speed-mode-bpm').classList.toggle('active', state.speedMode === 'bpm');
  speedSliderRow.style.display = (isSolid && state.speedMode === 'manual') ? '' : 'none';
  bpmRow.style.display         = (!isSolid || state.speedMode === 'bpm') ? '' : 'none';
  bpmDisplay.textContent       = state.bpm > 0 ? Math.round(state.bpm) + ' BPM' : '--';

  // Color picker
  const hex = rgbToHex(...state.params.color);
  colorPicker.value = hex;
  colorHex.textContent = hex;

  // Sliders (display as 0-100 integers)
  const bPct = toPct(state.params.brightness);
  brightnessEl.value      = bPct;
  brightnessVal.textContent = bPct + '%';

  const sPct = toPct(state.params.speed);
  speedEl.value      = sPct;
  speedVal.textContent = sPct + '%';
}

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------
powerBtn.addEventListener('click', async () => {
  const on = !state.power;
  if (await post('/api/power', { on })) {
    applyState({ power: on });
  }
});

animGrid.addEventListener('click', async (e) => {
  const btn = e.target.closest('.anim-btn');
  if (!btn) return;
  const name = btn.dataset.name;
  if (await post('/api/animation', { name })) {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        applyState(data);
        if (data.animation === 'solid' && data.speed_mode === 'manual') stopBpmPoll();
        else startBpmPoll();
        return;
      }
    } catch (_) {}
    applyState({ animation: name });
  }
});

colorPicker.addEventListener('input', debounce(async (e) => {
  const color = hexToRgb(e.target.value);
  colorHex.textContent = e.target.value;
  if (await post('/api/params', { color })) {
    applyState({ params: { color } });
  }
}, 80));

brightnessEl.addEventListener('input', (e) => {
  brightnessVal.textContent = e.target.value + '%';
});
brightnessEl.addEventListener('change', debounce(async (e) => {
  const brightness = toFloat(e.target.value);
  if (await post('/api/params', { brightness })) {
    applyState({ params: { brightness } });
  }
}, 50));

speedEl.addEventListener('input', (e) => {
  speedVal.textContent = e.target.value + '%';
});
speedEl.addEventListener('change', debounce(async (e) => {
  const speed = toFloat(e.target.value);
  if (await post('/api/params', { speed })) {
    applyState({ params: { speed } });
  }
}, 50));

speedModeToggle.addEventListener('click', async (e) => {
  const btn = e.target.closest('.mode-btn[data-mode]');
  if (!btn) return;
  const mode = btn.dataset.mode;
  if (mode === state.speedMode) return;
  if (await post('/api/speed_mode', { mode })) {
    applyState({ speed_mode: mode });
    if (mode === 'bpm') startBpmPoll(); else stopBpmPoll();
  }
});

// ---------------------------------------------------------------------------
// Custom animation controls — dynamically rendered from param_schema
// ---------------------------------------------------------------------------
function renderCustomControls() {
  const entries = Object.entries(state.paramSchema);
  customControlsCard.style.display = entries.length ? '' : 'none';
  customControls.innerHTML = '';

  entries.forEach(([key, meta], i) => {
    const current = toPct(state.params[key] ?? meta.default);
    const wrap = document.createElement('div');
    if (i > 0) wrap.className = 'custom-param';
    wrap.innerHTML =
      '<p class="param-label">' + meta.label + '</p>' +
      '<div class="slider-row">' +
        '<span class="slider-label">Low</span>' +
        '<input type="range" id="custom-' + key + '" min="0" max="100" step="1" value="' + current + '">' +
        '<span class="slider-label">High</span>' +
        '<span id="custom-' + key + '-val" class="slider-value">' + current + '%</span>' +
      '</div>';
    customControls.appendChild(wrap);

    const slider = document.getElementById('custom-' + key);
    const valEl  = document.getElementById('custom-' + key + '-val');
    slider.addEventListener('input', () => { valEl.textContent = slider.value + '%'; });
    slider.addEventListener('change', debounce(async () => {
      const value = toFloat(slider.value);
      if (await post('/api/params', { [key]: value })) {
        state.params[key] = value;
      }
    }, 50));
  });
}

function syncCustomSliders() {
  for (const key of Object.keys(state.paramSchema)) {
    const el = document.getElementById('custom-' + key);
    if (el && key in state.params) {
      el.value = toPct(state.params[key]);
      const valEl = document.getElementById('custom-' + key + '-val');
      if (valEl) valEl.textContent = el.value + '%';
    }
  }
}

// ---------------------------------------------------------------------------
// BPM polling — active only when speed mode is 'bpm'
// ---------------------------------------------------------------------------
let _bpmPollTimer = null;

function startBpmPoll() {
  if (_bpmPollTimer) return;
  _bpmPollTimer = setInterval(async () => {
    try {
      const res = await fetch('/api/status');
      if (res.ok) applyState({ bpm: (await res.json()).bpm });
    } catch (_) {}
  }, 1000);
}

function stopBpmPoll() {
  if (_bpmPollTimer) { clearInterval(_bpmPollTimer); _bpmPollTimer = null; }
}

// ---------------------------------------------------------------------------
// Bootstrap: sync UI with server state on page load
// ---------------------------------------------------------------------------
(async () => {
  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      const data = await res.json();
      applyState(data);
      if (!(data.animation === 'solid' && data.speed_mode === 'manual')) startBpmPoll();
      return;
    }
  } catch (_) {}
  applyState(state);
  startBpmPoll();  // default is BPM mode
})();
