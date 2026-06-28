import random
from animations.base import BaseAnimation


def _wheel(pos):
    pos = pos % 256
    if pos < 85:
        return 255 - pos * 3, pos * 3, 0
    if pos < 170:
        pos -= 85
        return 0, 255 - pos * 3, pos * 3
    pos -= 170
    return pos * 3, 0, 255 - pos * 3


class CometStormAnimation(BaseAnimation):
    """Each of the 12 frequency bands has a home position along the strip.
    When a band's energy spikes it launches comets outward from that position,
    rainbow-coloured by band index.  High-energy bands fire in both directions
    and more frequently; quiet bands fire sporadically in one direction.
    """

    name = "comet_storm"
    audio_reactive = True

    PARAM_SCHEMA = {
        "tail":        {"label": "Tail Length",  "default": 0.65},
        "hue":         {"label": "Hue Shift",    "default": 0.0},
        "spread":      {"label": "Color Spread", "default": 1.0},
        "sensitivity": {"label": "Sensitivity",  "default": 0.5},
        "density":     {"label": "Density",      "default": 0.5},
    }

    _MIN_CD = 4  # minimum frames between launches per band

    def __init__(self):
        super().__init__()
        self._comets    = []
        self._pixels    = []
        self._cooldowns = {}  # band_idx → remaining cooldown frames

    def update(self, strip, num_leds):
        speed       = self._params["speed"]
        brightness  = self._params["brightness"]
        tail        = self._params["tail"]
        hue_shift   = int(self._params["hue"] * 256)
        spread      = self._params["spread"]
        sensitivity = self._params["sensitivity"]
        density     = self._params["density"]
        audio       = self._audio_data or {}
        bands       = audio.get("spectrum") or []
        num_bands   = len(bands)

        # sensitivity 1.0 → threshold 0.05 (very reactive); 0.0 → 0.3 (loud hits only)
        threshold = 0.3 - sensitivity * 0.25

        if len(self._pixels) != num_leds:
            self._pixels = [(0.0, 0.0, 0.0)] * num_leds

        # Each band spawns comets from its fixed position along the strip
        for band_idx in range(num_bands):
            level = float(bands[band_idx])

            cd = self._cooldowns.get(band_idx, 0)
            if cd > 0:
                self._cooldowns[band_idx] = cd - 1
                continue

            if level < threshold:
                continue

            pos     = (band_idx + 0.5) * num_leds / num_bands
            hue     = int(hue_shift + band_idx * 256 * spread / num_bands) % 256
            r, g, b = _wheel(hue)
            vel_mag = 0.4 + speed * 2.0

            # High-energy bands fire in both directions; low-energy pick one
            directions = [-1, 1] if level > 0.4 else [random.choice([-1, 1])]
            for d in directions:
                self._comets.append({
                    "pos":   float(pos),
                    "vel":   vel_mag * d,
                    "color": (r, g, b),
                })

            # density 1.0 → short cooldown (dense); 0.0 → long cooldown (sparse)
            base_cd = max(self._MIN_CD, int(12 * (1.0 - level)))
            self._cooldowns[band_idx] = max(self._MIN_CD, int(base_cd * (1.5 - density)))

        # Tail decay (tail=0 → decay 0.55 sharp, tail=1 → decay 0.97 long glow)
        decay = 0.55 + tail * 0.42
        self._pixels = [
            (r * decay, g * decay, b * decay)
            for r, g, b in self._pixels
        ]

        # Advance comets and paint into the pixel buffer
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

        for i in range(num_leds):
            r, g, b = self._pixels[i]
            strip.set_pixel(i, *self._scale(int(r), int(g), int(b)))

        self.frame += 1
