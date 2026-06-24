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


class SpectrumAnimation(BaseAnimation):
    name = "spectrum"
    audio_reactive = True

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        audio = self._audio_data or {}
        bands = audio.get("spectrum") or []

        num_bands = len(bands) if bands else 1
        leds_per_band = num_leds // num_bands

        for band_idx in range(num_bands):
            level = float(bands[band_idx]) if bands else 0.0
            lit = int(level * leds_per_band)
            hue = int(band_idx * 256 / num_bands)
            r, g, b = _wheel(hue)

            for j in range(leds_per_band):
                led_idx = band_idx * leds_per_band + j
                if led_idx >= num_leds:
                    break
                if j < lit:
                    strip.set_pixel(led_idx, *self._scale(r, g, b, brightness))
                else:
                    strip.set_pixel(led_idx, 0, 0, 0)

        # Dark out any remainder LEDs when num_leds % num_bands != 0
        for i in range(num_bands * leds_per_band, num_leds):
            strip.set_pixel(i, 0, 0, 0)

        self.frame += 1
