from animations.base import BaseAnimation


class BeatPulseAnimation(BaseAnimation):
    name = "beat_pulse"
    audio_reactive = True

    def __init__(self):
        super().__init__()
        self._intensity = 0.0

    def update(self, strip, num_leds):
        r, g, b = self._params["color"]
        brightness = self._params["brightness"]
        speed = self._params["speed"]
        audio = self._audio_data or {}

        if audio.get("beat", False):
            self._intensity = 1.0

        scaled = self._scale(r, g, b, brightness * self._intensity)
        for i in range(num_leds):
            strip.set_pixel(i, *scaled)

        # speed 0.0-1.0: low = slow romantic fade, high = sharp strobe snap
        decay = 0.03 + speed * 0.12
        self._intensity = max(0.0, self._intensity - decay)
        self.frame += 1
