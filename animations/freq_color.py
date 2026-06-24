import math
from animations.base import BaseAnimation


def _hsv_to_rgb(h, s, v):
    """h: 0-360, s/v: 0.0-1.0 -> (r, g, b) 0-255."""
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


_LOG_LOW = math.log10(20)
_LOG_HIGH = math.log10(20000)


class FreqColorAnimation(BaseAnimation):
    name = "freq_color"
    audio_reactive = True

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        audio = self._audio_data or {}
        volume = max(0.0, min(1.0, audio.get("volume", 0.0)))
        dominant_freq = max(20.0, audio.get("dominant_freq", 200.0))

        # Map log-frequency (20 Hz – 20 kHz) to hue (0 – 360°)
        hue = (math.log10(dominant_freq) - _LOG_LOW) / (_LOG_HIGH - _LOG_LOW) * 360

        r, g, b = _hsv_to_rgb(hue, 1.0, 1.0)
        # Volume modulates brightness; floor at 0.05 so the color stays visible
        effective = brightness * max(0.05, volume)

        scaled = self._scale(r, g, b, effective)
        for i in range(num_leds):
            strip.set_pixel(i, *scaled)

        self.frame += 1
