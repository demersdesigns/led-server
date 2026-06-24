from animations.base import BaseAnimation


class ChaseAnimation(BaseAnimation):
    name = "chase"

    def update(self, strip, num_leds):
        r, g, b = self._params["color"]
        speed = self._params["speed"]

        # speed 0.0-1.0 -> 1 step every 180 frames down to every frame
        frames_per_step = max(1, int((1 - speed) * 179 + 1))
        offset = (self.frame // frames_per_step) % 3

        lit = self._scale(r, g, b)
        for i in range(num_leds):
            if i % 3 == offset:
                strip.set_pixel(i, *lit)
            else:
                strip.set_pixel(i, 0, 0, 0)
        self.frame += 1
