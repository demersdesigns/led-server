import math
from animations.base import BaseAnimation

_RING_WIDTH = 2.5   # half-width of the wavefront pulse in pixels

_LOG_LOW  = math.log10(20.0)
_LOG_HIGH = math.log10(20000.0)


def _freq_to_rgb(freq):
    """Map dominant frequency (log 20–20 kHz) to a saturated hue."""
    hue = (math.log10(max(20.0, freq)) - _LOG_LOW) / (_LOG_HIGH - _LOG_LOW) * 360.0
    x = 1.0 - abs((hue / 60.0) % 2 - 1.0)
    if   hue < 60:  r, g, b = 1.0,   x, 0.0
    elif hue < 120: r, g, b =   x, 1.0, 0.0
    elif hue < 180: r, g, b = 0.0, 1.0,   x
    elif hue < 240: r, g, b = 0.0,   x, 1.0
    elif hue < 300: r, g, b =   x, 0.0, 1.0
    else:           r, g, b = 1.0, 0.0,   x
    return int(r * 255), int(g * 255), int(b * 255)


class RippleAnimation(BaseAnimation):
    name = "ripple"
    audio_reactive = True

    def __init__(self):
        super().__init__()
        self._ripples = []      # list of {"radius": float, "color": (r, g, b)}
        self._prev_beat = False

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        speed      = self._params["speed"]
        audio      = self._audio_data or {}

        beat          = audio.get("beat", False)
        dominant_freq = audio.get("dominant_freq", 200.0)

        # Spawn one ripple per beat on the rising edge only
        if beat and not self._prev_beat:
            self._ripples.append({
                "radius": 0.0,
                "color": _freq_to_rgb(dominant_freq),
            })
        self._prev_beat = beat

        # Advance ripples; cull any that have cleared the strip edge
        center     = num_leds / 2.0
        max_radius = center + _RING_WIDTH
        step       = 0.3 + speed * 1.2     # 0.3–1.5 pixels per frame
        for ripple in self._ripples:
            ripple["radius"] += step
        self._ripples = [r for r in self._ripples if r["radius"] < max_radius]

        # Render: sum contributions from every in-flight ripple per LED
        for i in range(num_leds):
            dist = abs(i + 0.5 - center)   # distance of LED midpoint from strip center
            r_acc = g_acc = b_acc = 0
            for ripple in self._ripples:
                proximity = abs(dist - ripple["radius"])
                if proximity >= _RING_WIDTH:
                    continue
                envelope    = (1.0 - proximity / _RING_WIDTH) ** 2  # quadratic falloff
                travel_fade = max(0.0, 1.0 - ripple["radius"] / max_radius)
                intensity   = envelope * travel_fade * brightness
                rc, gc, bc  = ripple["color"]
                r_acc += int(rc * intensity)
                g_acc += int(gc * intensity)
                b_acc += int(bc * intensity)
            strip.set_pixel(i, min(255, r_acc), min(255, g_acc), min(255, b_acc))

        self.frame += 1
