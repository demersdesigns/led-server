import random
from animations.base import BaseAnimation

_DECAY = 0.06  # intensity lost per frame


class TwinkleAnimation(BaseAnimation):
    name = "twinkle"

    def __init__(self):
        super().__init__()
        self._intensities = []

    def update(self, strip, num_leds):
        r, g, b = self._params["color"]
        brightness = self._params["brightness"]
        speed = self._params["speed"]

        if len(self._intensities) != num_leds:
            self._intensities = [0.0] * num_leds

        # speed 0.0-1.0 -> spark probability 0.01-0.10 per LED per frame
        spawn_prob = 0.01 + speed * 0.09

        for i in range(num_leds):
            if random.random() < spawn_prob:
                self._intensities[i] = 1.0
            v = self._intensities[i]
            strip.set_pixel(i, *self._scale(r, g, b, brightness * v))
            self._intensities[i] = max(0.0, v - _DECAY)

        self.frame += 1
