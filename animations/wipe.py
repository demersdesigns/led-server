from animations.base import BaseAnimation


class WipeAnimation(BaseAnimation):
    name = "wipe"

    def update(self, strip, num_leds):
        r, g, b = self._params["color"]
        speed = self._params["speed"]

        # speed 0.0-1.0 -> 1 pixel every 10 frames down to every frame
        frames_per_step = max(1, int((1 - speed) * 9 + 1))
        # Full cycle: num_leds steps to wipe on + num_leds steps to wipe off
        step = (self.frame // frames_per_step) % (num_leds * 2)

        lit = self._scale(r, g, b)
        if step < num_leds:
            for i in range(num_leds):
                strip.set_pixel(i, *(lit if i <= step else (0, 0, 0)))
        else:
            pos = step - num_leds
            for i in range(num_leds):
                strip.set_pixel(i, *((0, 0, 0) if i <= pos else lit))
        self.frame += 1
