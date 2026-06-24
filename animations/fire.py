import random
from animations.base import BaseAnimation

_COOLING = 55
_SPARKING = 120


def _heat_to_rgb(heat):
    """Map heat 0-255 to fire color: black -> red -> yellow -> white."""
    t = heat / 255.0
    if t < 0.33:
        return int(t / 0.33 * 255), 0, 0
    if t < 0.66:
        return 255, int((t - 0.33) / 0.33 * 255), 0
    return 255, 255, int((t - 0.66) / 0.34 * 255)


class FireAnimation(BaseAnimation):
    name = "fire"

    def __init__(self):
        super().__init__()
        self._heat = []

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        speed = self._params["speed"]

        # speed 0.0-1.0 -> physics runs every 5 frames down to every frame
        frames_per_step = max(1, int((1 - speed) * 4 + 1))

        if len(self._heat) != num_leds:
            self._heat = [0] * num_leds

        if self.frame % frames_per_step == 0:
            # Cool each cell
            for i in range(num_leds):
                cool = random.randint(0, (_COOLING * 10) // num_leds + 2)
                self._heat[i] = max(0, self._heat[i] - cool)

            # Heat drifts upward
            for i in range(num_leds - 1, 1, -1):
                self._heat[i] = (
                    self._heat[i - 1] + self._heat[i - 2] + self._heat[i - 2]
                ) // 3

            # Random sparks at the base
            if random.randint(0, 255) < _SPARKING:
                idx = random.randint(0, min(7, num_leds - 1))
                self._heat[idx] = min(255, self._heat[idx] + random.randint(160, 255))

        for i in range(num_leds):
            r, g, b = _heat_to_rgb(self._heat[i])
            strip.set_pixel(i, *self._scale(r, g, b, brightness))

        self.frame += 1
