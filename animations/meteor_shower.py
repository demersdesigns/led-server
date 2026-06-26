import math
import random
from animations.base import BaseAnimation

_TAIL_DECAY = 0.82   # per-frame multiplier; lower = shorter tail

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


class MeteorShowerAnimation(BaseAnimation):
    name = "meteor_shower"
    audio_reactive = True

    def __init__(self):
        super().__init__()
        self._comets = []    # list of {"pos": float, "vel": float, "color": (r, g, b)}
        self._pixels = []    # float (r, g, b) buffer — decays each frame to form tails
        self._prev_beat = False

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        speed      = self._params["speed"]
        audio      = self._audio_data or {}

        beat          = audio.get("beat", False)
        volume        = max(0.0, min(1.0, audio.get("volume", 0.0)))
        dominant_freq = audio.get("dominant_freq", 200.0)

        if len(self._pixels) != num_leds:
            self._pixels = [(0.0, 0.0, 0.0)] * num_leds

        # On the rising edge of each beat, launch 1–5 comets based on volume
        if beat and not self._prev_beat:
            count = 1 + int(volume * 4)
            color = _freq_to_rgb(dominant_freq)
            vel_mag = 0.5 + speed * 2.0     # 0.5–2.5 pixels per frame
            for _ in range(count):
                self._comets.append({
                    "pos":   random.uniform(0, num_leds - 1),
                    "vel":   vel_mag * random.choice([-1, 1]),
                    "color": color,
                })
        self._prev_beat = beat

        # Decay every pixel to form the tail behind each moving comet
        self._pixels = [
            (r * _TAIL_DECAY, g * _TAIL_DECAY, b * _TAIL_DECAY)
            for r, g, b in self._pixels
        ]

        # Advance each comet and paint its head into the buffer; cull off-strip comets
        live = []
        for comet in self._comets:
            comet["pos"] += comet["vel"]
            idx = int(comet["pos"])
            if 0 <= idx < num_leds:
                cr, cg, cb = comet["color"]
                pr, pg, pb = self._pixels[idx]
                self._pixels[idx] = (
                    min(255.0, pr + cr),
                    min(255.0, pg + cg),
                    min(255.0, pb + cb),
                )
                live.append(comet)
        self._comets = live

        # Write buffer to strip, scaled by brightness
        for i in range(num_leds):
            r, g, b = self._pixels[i]
            strip.set_pixel(i, *self._scale(int(r), int(g), int(b)))

        self.frame += 1
