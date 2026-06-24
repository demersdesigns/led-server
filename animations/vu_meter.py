from animations.base import BaseAnimation


class VuMeterAnimation(BaseAnimation):
    name = "vu_meter"
    audio_reactive = True

    def update(self, strip, num_leds):
        brightness = self._params["brightness"]
        audio = self._audio_data or {}
        volume = max(0.0, min(1.0, audio.get("volume", 0.0)))

        lit = int(volume * num_leds)

        for i in range(num_leds):
            if i < lit:
                frac = i / num_leds
                if frac < 0.6:
                    r, g = 0, 255                               # green
                elif frac < 0.8:
                    t = (frac - 0.6) / 0.2
                    r, g = int(t * 255), 255                    # green -> yellow
                else:
                    t = (frac - 0.8) / 0.2
                    r, g = 255, int((1 - t) * 255)              # yellow -> red
                strip.set_pixel(i, *self._scale(r, g, 0, brightness))
            else:
                strip.set_pixel(i, 0, 0, 0)

        self.frame += 1
