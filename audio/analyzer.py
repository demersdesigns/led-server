import logging
import threading
import time

import numpy as np

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    HAS_AUDIO = True
except ImportError:
    sd = None
    HAS_AUDIO = False
    logger.warning("sounddevice not available; audio features disabled")

from config import (
    AUDIO_CHUNK,
    AUDIO_CHANNELS,
    AUDIO_DEVICE_NAME,
    AUDIO_SAMPLE_RATE,
    BEAT_HISTORY,
    BEAT_THRESHOLD,
    BPM_HISTORY,
    BPM_MIN,
    BPM_MAX,
    FFT_BANDS,
)

_FREQ_LOW = 20.0
_FREQ_HIGH = 20000.0
_RECONNECT_INTERVAL = 5.0  # seconds between reconnect attempts
_BEAT_BASS_LOW  = 20.0    # kick drum fundamental range — low end
_BEAT_BASS_HIGH = 200.0   # kick drum fundamental range — high end


class AudioAnalyzer:
    """Captures audio from the Zoom H6 (stereo, class-compliant) and exposes
    per-frame analysis results to audio-reactive animations via get_data().

    Must be used in stereo mode on the H6 — the device is not class-compliant
    in multi-track mode and will not appear as a standard USB audio device.

    Includes a watchdog thread that reconnects automatically if the stream
    drops or the device wasn't present at startup.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._volume = 0.0
        self._beat = False
        self._spectrum = [0.0] * FFT_BANDS
        self._dominant_freq = 200.0

        self._stream = None
        self._running = False  # controls watcher thread lifetime

        # Circular buffer of per-chunk energy for beat detection
        self._energy_history = np.zeros(BEAT_HISTORY)
        self._history_idx = 0

        # BPM tracking: timestamps of recent beat onsets → median IBI
        self._beat_times = []    # list of monotonic timestamps (max BPM_HISTORY+1)
        self._bpm = 0.0
        self._prev_beat_cb = False   # rising-edge tracker for callback thread
        self._prev_bass_fft = None   # previous frame's bass FFT for spectral flux

        # Precompute log-spaced band edges once
        self._band_edges = np.logspace(
            np.log10(_FREQ_LOW), np.log10(_FREQ_HIGH), FFT_BANDS + 1
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        if not HAS_AUDIO:
            logger.warning("Audio disabled — sounddevice not installed")
            return
        self._running = True
        self._try_start_stream()
        t = threading.Thread(target=self._watcher, daemon=True, name="audio-watcher")
        t.start()

    def stop(self):
        self._running = False
        self._close_stream()

    def get_data(self):
        """Thread-safe snapshot of the latest analysis frame."""
        with self._lock:
            return {
                "volume": self._volume,
                "beat": self._beat,
                "spectrum": list(self._spectrum),
                "dominant_freq": self._dominant_freq,
                "bpm": self._bpm,
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _close_stream(self):
        stream = self._stream
        self._stream = None
        if stream:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

    def _try_start_stream(self):
        """Attempt to open the audio input stream. Safe to call repeatedly."""
        self._close_stream()
        device_idx = self._find_device()
        try:
            stream = sd.InputStream(
                device=device_idx,   # None → sounddevice system default
                channels=AUDIO_CHANNELS,
                samplerate=AUDIO_SAMPLE_RATE,
                blocksize=AUDIO_CHUNK,
                dtype="float32",
                callback=self._callback,
            )
            stream.start()
            self._stream = stream
            logger.info("Audio stream started (device=%s)", device_idx)
        except Exception:
            logger.warning(
                "Audio stream start failed; will retry in %.0fs", _RECONNECT_INTERVAL
            )

    def _watcher(self):
        """Daemon thread: polls stream health and reconnects on failure."""
        while self._running:
            time.sleep(_RECONNECT_INTERVAL)
            if not self._running:
                break
            stream_ok = self._stream is not None and self._stream.active
            if not stream_ok:
                logger.info("Audio stream inactive; reconnecting...")
                self._try_start_stream()

    def _find_device(self):
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if (
                AUDIO_DEVICE_NAME.lower() in dev["name"].lower()
                and dev["max_input_channels"] > 0
            ):
                logger.info("Using audio device %d: %s", idx, dev["name"])
                return idx
        logger.warning(
            "Audio device '%s' not found; available input devices: %s",
            AUDIO_DEVICE_NAME,
            [d["name"] for d in devices if d["max_input_channels"] > 0],
        )
        return None

    def _callback(self, indata, frames, time_info, status):
        if status:
            logger.warning("Audio stream status: %s", status)

        # Average stereo channels to mono — H6 is always stereo in this mode
        mono = indata.mean(axis=1) if indata.ndim > 1 else indata.flatten()

        # --- Volume: RMS normalized so typical music sits around 0.3-0.8 ---
        rms = float(np.sqrt(np.mean(mono ** 2)))
        volume = min(1.0, rms * 10.0)

        # --- FFT ---
        n = len(mono)
        windowed = mono * np.hanning(n)
        fft_mag = np.abs(np.fft.rfft(windowed))
        freqs = np.fft.rfftfreq(n, d=1.0 / AUDIO_SAMPLE_RATE)

        # Per-band energy across log-spaced frequency bins
        bands = np.zeros(FFT_BANDS)
        for i in range(FFT_BANDS):
            mask = (freqs >= self._band_edges[i]) & (freqs < self._band_edges[i + 1])
            if mask.any():
                bands[i] = float(np.mean(fft_mag[mask]))

        # Normalise relative frequency shape (0-1), then re-scale by volume so
        # that quiet signals produce small bars, not a falsely full spectrum.
        max_val = bands.max()
        if max_val > 0:
            bands = (bands / max_val) * volume

        # --- Dominant frequency ---
        peak_idx = int(np.argmax(fft_mag))
        dom_freq = float(freqs[peak_idx]) if peak_idx < len(freqs) else 200.0
        dom_freq = max(_FREQ_LOW, dom_freq)

        # --- Beat detection: bass spectral flux vs. rolling ~1-second average ---
        # Flux = sum of *positive* differences between this frame and the last
        # in the bass band (20-200 Hz). This detects the sharp attack of a kick
        # drum without being confused by sustained bass lines or 808s — those
        # produce near-zero flux after their initial hit.
        bass_mask = (freqs >= _BEAT_BASS_LOW) & (freqs < _BEAT_BASS_HIGH)
        bass_fft  = fft_mag[bass_mask]
        if self._prev_bass_fft is not None and len(self._prev_bass_fft) == len(bass_fft):
            flux = float(np.sum(np.maximum(0.0, bass_fft - self._prev_bass_fft)))
        else:
            flux = 0.0
        self._prev_bass_fft = bass_fft
        avg_flux = float(np.mean(self._energy_history))
        beat = avg_flux > 0 and flux > BEAT_THRESHOLD * avg_flux
        self._energy_history[self._history_idx] = flux
        self._history_idx = (self._history_idx + 1) % BEAT_HISTORY

        # --- BPM: track beat onsets, compute median inter-beat interval ---
        bpm = self._bpm
        if beat and not self._prev_beat_cb:
            now = time.monotonic()
            self._beat_times.append(now)
            if len(self._beat_times) > BPM_HISTORY + 1:
                self._beat_times.pop(0)
            if len(self._beat_times) >= 3:  # need at least 2 intervals
                intervals = [
                    self._beat_times[i + 1] - self._beat_times[i]
                    for i in range(len(self._beat_times) - 1)
                ]
                median_ibi = sorted(intervals)[len(intervals) // 2]
                if median_ibi > 0:
                    raw = 60.0 / median_ibi
                    bpm = max(BPM_MIN, min(BPM_MAX, raw))
        self._prev_beat_cb = beat

        with self._lock:
            self._volume = volume
            self._beat = beat
            self._spectrum = bands.tolist()
            self._dominant_freq = dom_freq
            self._bpm = bpm
