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


class MirrorBarsAnimation(BaseAnimation):
    name = "mirror_bars"
    audio_reactive = True

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        speed      = self._params["speed"]
        audio      = self._audio_data or {}
        bands      = audio.get("spectrum") or []

        # speed repurposed as sensitivity (same mapping as the old spectrum animation)
        gain = 4 ** (speed * 2 - 1)

        num_bands    = len(bands) if bands else 1
        half         = num_leds // 2
        leds_per_band = half // num_bands

        # Each band occupies a slot growing outward from center on both sides.
        # Band 0 (bass) is nearest the center; band N-1 (treble) is at the edges.
        for band_idx in range(num_bands):
            level = min(1.0, float(bands[band_idx]) * gain) if bands else 0.0
            lit   = int(level * leds_per_band)
            hue   = int(band_idx * 256 / num_bands)
            r, g, b = _wheel(hue)
            color   = self._scale(r, g, b, brightness)
            off     = (0, 0, 0)

            for j in range(leds_per_band):
                # Left half: center is index (half-1), band grows leftward
                left_idx  = half - 1 - band_idx * leds_per_band - j
                # Right half: center is index half, band grows rightward
                right_idx = half + band_idx * leds_per_band + j

                pixel = color if j < lit else off
                if 0 <= left_idx < num_leds:
                    strip.set_pixel(left_idx, *pixel)
                if 0 <= right_idx < num_leds:
                    strip.set_pixel(right_idx, *pixel)

        # Dark out any remainder LEDs when num_leds // 2 % num_bands != 0
        used = num_bands * leds_per_band
        for j in range(used, half):
            strip.set_pixel(half - 1 - j, 0, 0, 0)
            strip.set_pixel(half + j, 0, 0, 0)

        self.frame += 1
