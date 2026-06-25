import logging
import threading
import time

from config import (
    DEFAULT_ANIMATION,
    GLOBAL_BRIGHTNESS,
    NUM_LEDS,
    TARGET_FPS,
)

logger = logging.getLogger(__name__)

try:
    from apa102_pi.driver import apa102 as _driver
    HAS_HARDWARE = True
except ImportError:
    _driver = None
    HAS_HARDWARE = False
    logger.warning("apa102-pi not available; running in stub mode (no SPI output)")


class LEDController:
    """Owns the APA102 strip and drives the animation loop in a background thread.

    Animations own their own parameters (get_params / set_params).  The
    controller preserves the current param set when switching animations so
    speed and brightness survive the transition.
    """

    def __init__(self, audio_analyzer=None):
        self._num_leds = NUM_LEDS
        self._audio = audio_analyzer
        self._power = True
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        if HAS_HARDWARE:
            self._strip = _driver.APA102(
                num_led=NUM_LEDS,
                global_brightness=GLOBAL_BRIGHTNESS,
                mosi=10,
                sclk=11,
            )
        else:
            self._strip = None

        # Import deferred to avoid a circular import at module level
        from animations import ANIMATIONS
        self._ANIMATIONS = ANIMATIONS

        anim_cls = ANIMATIONS.get(DEFAULT_ANIMATION)
        self._animation = anim_cls() if anim_cls else None
        self._current_name = DEFAULT_ANIMATION if anim_cls else None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="led-loop")
        self._thread.start()
        logger.info("LED controller started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self._clear()
        if self._strip:
            self._strip.cleanup()
        logger.info("LED controller stopped")

    # ------------------------------------------------------------------
    # Public control API
    # ------------------------------------------------------------------

    def set_animation(self, name):
        """Switch to a named animation, preserving current params where possible."""
        anim_cls = self._ANIMATIONS.get(name)
        if not anim_cls:
            raise ValueError(f"Unknown animation: {name!r}")
        with self._lock:
            old_params = self._animation.get_params() if self._animation else {}
            self._animation = anim_cls()
            self._animation.set_params(old_params)
            self._current_name = name

    def set_params(self, params):
        """Update parameters on the current animation (e.g. speed, brightness, color)."""
        with self._lock:
            if self._animation:
                self._animation.set_params(params)

    def get_params(self):
        with self._lock:
            return self._animation.get_params() if self._animation else {}

    def set_power(self, on):
        with self._lock:
            self._power = bool(on)
        if not on:
            self._clear()

    def get_status(self):
        """Return a JSON-serialisable status dict for the /api/status route."""
        with self._lock:
            params = self._animation.get_params() if self._animation else {}
            audio_active = (
                self._audio is not None
                and getattr(self._audio, "_running", False)
            )
            return {
                "animation": self._current_name,
                "power": self._power,
                "params": params,
                "audio_active": audio_active,
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _clear(self):
        if self._strip:
            for i in range(self._num_leds):
                self._strip.set_pixel(i, 0, 0, 0)
            self._strip.show()

    def _loop(self):
        interval = 1.0 / TARGET_FPS
        while self._running:
            t0 = time.monotonic()

            with self._lock:
                power = self._power
                anim = self._animation

            if power and anim and self._strip:
                # Provide fresh audio data to reactive animations each frame
                if anim.audio_reactive and self._audio:
                    anim.audio_data = self._audio.get_data()

                try:
                    anim.update(self._strip, self._num_leds)
                    self._strip.show()
                except Exception:
                    logger.exception("Error in animation frame")

            remaining = interval - (time.monotonic() - t0)
            if remaining > 0:
                time.sleep(remaining)
