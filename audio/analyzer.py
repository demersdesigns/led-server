import logging
import threading

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
    FFT_BANDS,
)

_FREQ_LOW = 20.0
_FREQ_HIGH = 20000.0


class AudioAnalyzer:
    """Captures audio from the Zoom H6 (stereo, class-compliant) and exposes
    per-frame analysis results to audio-reactive animations via get_data().

    Must be used in stereo mode on the H6 — the device is not class-compliant
    in multi-track mode and will not appear as a standard USB audio device.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._volume = 0.0
        self._beat = False
        self._spectrum = [0.0] * FFT_BANDS
        self._dominant_freq = 200.0

        self._stream = None
        self._running = False

        # Circular buffer of per-chunk energy for beat detection
        self._energy_history = np.zeros(BEAT_HISTORY)
        self._history_idx = 0

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
        device_idx = self._find_device()
        if device_idx is None:
            logger.error("Audio device '%s' not found — audio-reactive animations will be inactive", AUDIO_DEVICE_NAME)
            return
        try:
            self._stream = sd.InputStream(
                device=device_idx,
                channels=AUDIO_CHANNELS,
                samplerate=AUDIO_SAMPLE_RATE,
                blocksize=AUDIO_CHUNK,
                dtype="float32",
                callback=self._callback,
            )
            self._stream.start()
            self._running = True
            logger.info("Audio stream started (device=%s)", device_idx)
        except Exception:
            logger.exception("Failed to start audio stream")

    def stop(self):
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                logger.exception("Error stopping audio stream")
            self._stream = None
        self._running = False

    def get_data(self):
        """Thread-safe snapshot of the latest analysis frame."""
        with self._lock:
            return {
                "volume": self._volume,
                "beat": self._beat,
                "spectrum": list(self._spectrum),
                "dominant_freq": self._dominant_freq,
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

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
            "Device '%s' not found; falling back to system default input",
            AUDIO_DEVICE_NAME,
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

        # --- Beat detection: local energy vs. rolling ~1-second average ---
        energy = float(np.sum(mono ** 2))
        avg_energy = float(np.mean(self._energy_history))
        beat = (
            avg_energy > 0
            and energy > BEAT_THRESHOLD * avg_energy
            and energy > 1e-4
        )
        self._energy_history[self._history_idx] = energy
        self._history_idx = (self._history_idx + 1) % BEAT_HISTORY

        with self._lock:
            self._volume = volume
            self._beat = beat
            self._spectrum = bands.tolist()
            self._dominant_freq = dom_freq
