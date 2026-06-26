'use strict';

// ---------------------------------------------------------------------------
// Client-side state — mirrors the shape returned by GET /api/status
// ---------------------------------------------------------------------------
const state = {
  animation:   'solid',
  power:       true,
  audioActive: false,
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
const speedEl        = document.getElementById('speed');
const speedVal       = document.getElementById('speed-val');
const speedHeading   = document.getElementById('speed-heading');
const speedMinLabel  = document.getElementById('speed-min-label');
const speedMaxLabel  = document.getElementById('speed-max-label');
const appEl          = document.querySelector('.app');

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
  if ('animation'   in s) state.animation   = s.animation;
  if ('power'       in s) state.power       = s.power;
  if ('audio_active' in s) state.audioActive = s.audio_active;

  // Merge nested params if present
  if (s.params) {
    if ('speed'      in s.params) state.params.speed      = s.params.speed;
    if ('brightness' in s.params) state.params.brightness = s.params.brightness;
    if ('color'      in s.params) state.params.color      = s.params.color;
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

  // Speed slider doubles as Sensitivity for the spectrum animation
  const isSpectrum = state.animation === 'spectrum';
  speedHeading.textContent  = isSpectrum ? 'Sensitivity' : 'Speed';
  speedMinLabel.textContent = isSpectrum ? 'Low'  : 'Slow';
  speedMaxLabel.textContent = isSpectrum ? 'High' : 'Fast';

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

// ---------------------------------------------------------------------------
// Bootstrap: sync UI with server state on page load
// ---------------------------------------------------------------------------
(async () => {
  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      applyState(await res.json());
      return;
    }
  } catch (_) {}
  applyState(state);  // fall back to JS defaults
})();
