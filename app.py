import logging

from flask import Flask, jsonify, render_template, request

from animations import ANIMATION_NAMES, AUDIO_REACTIVE_NAMES
from audio.analyzer import AudioAnalyzer
from led_controller import LEDController

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

audio = AudioAnalyzer()
controller = LEDController(audio_analyzer=audio)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        animation_names=ANIMATION_NAMES,
        audio_reactive_names=AUDIO_REACTIVE_NAMES,
    )


@app.route("/api/status")
def api_status():
    """Return current animation name, its parameters, and audio state."""
    return jsonify(controller.get_status())


@app.route("/api/animation", methods=["POST"])
def api_animation():
    """Switch the active animation.  Body: { "name": "rainbow" }"""
    data = request.get_json(force=True, silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"ok": False, "error": "Missing 'name'"}), 400
    try:
        controller.set_animation(name)
        return jsonify({"ok": True, "animation": name})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/params", methods=["POST"])
def api_params():
    """Update one or more animation parameters.

    Accepted keys (all optional):
      speed       float 0.0-1.0
      brightness  float 0.0-1.0
      color       [r, g, b]  (0-255 each)
    """
    data = request.get_json(force=True, silent=True) or {}
    params = {}

    if "speed" in data:
        params["speed"] = max(0.0, min(1.0, float(data["speed"])))

    if "brightness" in data:
        params["brightness"] = max(0.0, min(1.0, float(data["brightness"])))

    if "color" in data:
        c = data["color"]
        if isinstance(c, (list, tuple)) and len(c) == 3:
            params["color"] = [
                max(0, min(255, int(c[0]))),
                max(0, min(255, int(c[1]))),
                max(0, min(255, int(c[2]))),
            ]
        else:
            return jsonify({"ok": False, "error": "color must be [r, g, b]"}), 400

    # Custom animation params — validated against the active animation's schema
    for key in controller.get_param_schema():
        if key in data:
            try:
                params[key] = max(0.0, min(1.0, float(data[key])))
            except (TypeError, ValueError):
                pass

    controller.set_params(params)
    return jsonify({"ok": True, "params": controller.get_params()})


@app.route("/api/speed_mode", methods=["POST"])
def api_speed_mode():
    """Switch speed control between 'manual' (slider) and 'bpm' (audio tempo)."""
    data = request.get_json(force=True, silent=True) or {}
    mode = str(data.get("mode", "")).strip()
    if mode not in ("manual", "bpm"):
        return jsonify({"ok": False, "error": "mode must be 'manual' or 'bpm'"}), 400
    controller.set_speed_mode(mode)
    return jsonify({"ok": True, "speed_mode": mode})


@app.route("/api/off", methods=["POST"])
def api_off():
    """Turn off all LEDs immediately."""
    controller.set_power(False)
    return jsonify({"ok": True, "power": False})


@app.route("/api/power", methods=["POST"])
def api_power():
    """Toggle power on or off.  Body: { "on": true|false }"""
    data = request.get_json(force=True, silent=True) or {}
    on = bool(data.get("on", True))
    controller.set_power(on)
    return jsonify({"ok": True, "power": on})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        audio.start()
        controller.start()
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    finally:
        controller.stop()
        audio.stop()
