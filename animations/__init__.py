from animations.solid import SolidAnimation
from animations.breathe import BreatheAnimation
from animations.chase import ChaseAnimation
from animations.rainbow import RainbowAnimation
from animations.wipe import WipeAnimation
from animations.twinkle import TwinkleAnimation
from animations.fire import FireAnimation
from animations.comet import CometAnimation
from animations.vu_meter import VuMeterAnimation
from animations.ripple import RippleAnimation
from animations.meteor_shower import MeteorShowerAnimation
from animations.comet_storm import CometStormAnimation
from animations.beat_pulse import BeatPulseAnimation
from animations.freq_color import FreqColorAnimation

# Ordered list used for UI display
_ALL = [
    SolidAnimation,
    BreatheAnimation,
    ChaseAnimation,
    RainbowAnimation,
    WipeAnimation,
    TwinkleAnimation,
    FireAnimation,
    CometAnimation,
    VuMeterAnimation,
    RippleAnimation,
    MeteorShowerAnimation,
    CometStormAnimation,
    BeatPulseAnimation,
    FreqColorAnimation,
]

ANIMATIONS = {cls.name: cls for cls in _ALL}
ANIMATION_NAMES = [cls.name for cls in _ALL]
AUDIO_REACTIVE_NAMES = [cls.name for cls in _ALL if cls.audio_reactive]
