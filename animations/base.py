from abc import ABC, abstractmethod

from config import DEFAULT_BRIGHTNESS, DEFAULT_COLOR, DEFAULT_SPEED


class BaseAnimation(ABC):
    """Abstract base class for all LED animations.

    Animations own their configuration.  The controller calls:
      - set_params(dict)  to push new values from the web UI
      - get_params()      to read current values (e.g. for /api/status)
      - update(strip, num_leds)  once per frame

    Parameters are stored as normalized values:
      speed      float 0.0–1.0
      brightness float 0.0–1.0
      color      list  [r, g, b]  (0–255 each)
    """

    name = "base"
    audio_reactive = False

    # Subclasses may override to add or remove supported params.
    DEFAULT_PARAMS = {
        "speed": DEFAULT_SPEED,
        "brightness": DEFAULT_BRIGHTNESS,
        "color": list(DEFAULT_COLOR),
    }

    def __init__(self):
        self._params = {k: (list(v) if isinstance(v, (tuple, list)) else v)
                        for k, v in self.DEFAULT_PARAMS.items()}
        self._audio_data = None
        self.frame = 0

    # ------------------------------------------------------------------
    # Params API (called by LEDController)
    # ------------------------------------------------------------------

    def get_params(self):
        """Return a copy of the current parameter dict."""
        return {k: (list(v) if isinstance(v, list) else v)
                for k, v in self._params.items()}

    def set_params(self, params):
        """Merge *params* into current values; unknown keys are ignored."""
        for key, value in params.items():
            if key not in self._params:
                continue
            if key == "color":
                if isinstance(value, (list, tuple)) and len(value) == 3:
                    self._params["color"] = [
                        max(0, min(255, int(value[0]))),
                        max(0, min(255, int(value[1]))),
                        max(0, min(255, int(value[2]))),
                    ]
            elif key in ("speed", "brightness"):
                self._params[key] = max(0.0, min(1.0, float(value)))
            else:
                self._params[key] = value

    # ------------------------------------------------------------------
    # Audio data (set by LEDController before each frame for reactive anims)
    # ------------------------------------------------------------------

    @property
    def audio_data(self):
        return self._audio_data

    @audio_data.setter
    def audio_data(self, data):
        self._audio_data = data

    # ------------------------------------------------------------------
    # Frame rendering (must be implemented by every animation)
    # ------------------------------------------------------------------

    @abstractmethod
    def update(self, strip, num_leds):
        """Render one frame.

        Call strip.set_pixel(i, r, g, b) for each LED.
        Do NOT call strip.show() — the controller handles that.

        Args:
            strip:    APA102 driver instance
            num_leds: total LED count (int)
        """

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scale(self, r, g, b, brightness=None):
        """Scale RGB by a brightness factor (0.0–1.0).

        If *brightness* is omitted the animation's current brightness param
        is used.  Returns (r, g, b) as ints.
        """
        if brightness is None:
            brightness = self._params.get("brightness", 1.0)
        s = float(brightness)
        return int(r * s), int(g * s), int(b * s)
