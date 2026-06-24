import math
from animations.base import BaseAnimation


class BreatheAnimation(BaseAnimation):
    name = "breathe"

    def update(self, strip, num_leds):
        r, g, b = self._params["color"]
        brightness = self._params["brightness"]
        speed = self._params["speed"]

        # speed 0.0-1.0 -> frequency 0.2-2.0 Hz
        freq = 0.2 + speed * 1.8
        t = self.frame / 60.0
        envelope = (math.sin(2 * math.pi * freq * t) + 1) / 2  # 0.0-1.0

        scaled = self._scale(r, g, b, brightness * envelope)
        for i in range(num_leds):
            strip.set_pixel(i, *scaled)
        self.frame += 1
