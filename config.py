# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------
NUM_LEDS = 60
# SK9822: global brightness field always fixed at max (31).
# All dimming is done by scaling RGB values — never use intermediate
# hardware brightness values, as they cause flicker/gamma artifacts.
GLOBAL_BRIGHTNESS = 31

# ---------------------------------------------------------------------------
# Defaults  (speed and brightness are normalized floats 0.0–1.0)
# ---------------------------------------------------------------------------
DEFAULT_ANIMATION = "solid"
DEFAULT_SPEED = 0.5
DEFAULT_BRIGHTNESS = 0.1        # dim on boot — just visible
DEFAULT_COLOR = (255, 250, 240) # soft warm white

# ---------------------------------------------------------------------------
# Animation loop
# ---------------------------------------------------------------------------
TARGET_FPS = 60

# ---------------------------------------------------------------------------
# Audio  (Zoom H6 must be in Stereo mode — it is class-compliant there)
# ---------------------------------------------------------------------------
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2              # stereo — do not change to 1
AUDIO_CHUNK = 1024
AUDIO_DEVICE_NAME = "H6"       # substring match against sounddevice device list
FFT_BANDS = 12
BEAT_THRESHOLD = 1.5            # energy ratio vs. rolling average to flag a beat
BEAT_HISTORY = 43               # ~1 second of history at 44100/1024
