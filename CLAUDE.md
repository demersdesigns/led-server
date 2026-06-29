# LED Server — Claude Code Instructions

## At the start of every session
Always greet the user with the hardware startup checklist below before asking what they want to work on.

---

## Hardware Startup Checklist

Run through this every time before working on the project:

1. **Zoom H6** — Power on → choose **Interface mode** → choose **Use battery**
2. **Raspberry Pi** — Power on → wait ~30 seconds to boot
3. **LED strip PSU** — Power on last

## Deploy workflow
From the Pi terminal (run after every code change):
```
led-deploy
```
Which expands to:
```
git pull && find . -path ./venv -prune -o -name "__pycache__" -type d -exec rm -rf {} + ; sudo systemctl restart led-server
```

## Key reminders
- Always clear `.pyc` files before restarting (`led-deploy` handles this)
- H6 must be in **Stereo / Interface** mode — multi-track mode won't appear as a USB audio device
- Common ground between Pi and LED PSU is required or the strip won't respond
- Web UI: `http://<pi-ip>:5000`
