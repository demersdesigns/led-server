from animations.base import BaseAnimation


def _wheel(pos):
    """0-255 position on the color wheel -> (r, g, b)."""
    pos = pos % 256
    if pos < 85:
        return 255 - pos * 3, pos * 3, 0
    if pos < 170:
        pos -= 85
        return 0, 255 - pos * 3, pos * 3
    pos -= 170
    return pos * 3, 0, 255 - pos * 3


class RainbowAnimation(BaseAnimation):
    name = "rainbow"

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        speed = self._params["speed"]

        # speed 0.0-1.0 -> 0.05-3.0 hue units per frame
        hue_step = 0.05 + speed * 2.95
        hue_offset = (self.frame * hue_step) % 256

        for i in range(num_leds):
            hue = int(i * 256 / num_leds + hue_offset) % 256
            r, g, b = _wheel(hue)
            strip.set_pixel(i, *self._scale(r, g, b, brightness))
        self.frame += 1
