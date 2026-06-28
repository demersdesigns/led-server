from animations.base import BaseAnimation


class LarsonAnimation(BaseAnimation):
    """Classic bouncing-eye scanner with a fading trail."""

    name = "scanner"
    audio_reactive = False

    def __init__(self):
        super().__init__()
        self._pos  = 0.0
        self._dir  = 1
        self._buf  = []

    def update(self, strip, num_leds):
        speed      = self._params["speed"]
        brightness = self._params["brightness"]
        r, g, b    = self._params["color"]

        if len(self._buf) != num_leds:
            self._buf = [(0.0, 0.0, 0.0)] * num_leds

        vel = 0.5 + speed * 3.0
        self._pos += vel * self._dir
        if self._pos >= num_leds - 1:
            self._pos = float(num_leds - 1)
            self._dir = -1
        elif self._pos <= 0:
            self._pos = 0.0
            self._dir = 1

        self._buf = [(pr * 0.82, pg * 0.82, pb * 0.82) for pr, pg, pb in self._buf]

        cx = int(self._pos)
        for idx, w in [(cx, 1.0), (cx - 1, 0.5), (cx + 1, 0.5), (cx - 2, 0.15), (cx + 2, 0.15)]:
            if 0 <= idx < num_leds:
                pr, pg, pb = self._buf[idx]
                self._buf[idx] = (min(255.0, pr + r * w), min(255.0, pg + g * w), min(255.0, pb + b * w))

        for i in range(num_leds):
            fr, fg, fb = self._buf[i]
            strip.set_pixel(i, *self._scale(int(fr), int(fg), int(fb)))

        self.frame += 1
