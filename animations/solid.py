from animations.base import BaseAnimation


class SolidAnimation(BaseAnimation):
    name = "solid"

    def update(self, strip, num_leds):
        r, g, b = self._params["color"]
        scaled = self._scale(r, g, b)
        for i in range(num_leds):
            strip.set_pixel(i, *scaled)
        self.frame += 1
