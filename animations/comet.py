from animations.base import BaseAnimation

_TAIL = 14


class CometAnimation(BaseAnimation):
    name = "comet"

    def __init__(self):
        super().__init__()
        self._pos = 0.0

    def update(self, strip, num_leds):
        r, g, b = self._params["color"]
        brightness = self._params["brightness"]
        speed = self._params["speed"]

        # speed 0.0-1.0 -> 0.05-1.5 pixels per frame
        step = 0.05 + speed * 1.45
        self._pos = (self._pos + step) % (num_leds + _TAIL)
        head = int(self._pos)

        for i in range(num_leds):
            dist = head - i
            if 0 <= dist < _TAIL:
                fade = (1.0 - dist / _TAIL) ** 2   # quadratic tail falloff
                strip.set_pixel(i, *self._scale(r, g, b, brightness * fade))
            else:
                strip.set_pixel(i, 0, 0, 0)

        self.frame += 1
