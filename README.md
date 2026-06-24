# LED Server

A Raspberry Pi LED strip controller for SK9822 (APA102-compatible) strips with a web-based control interface.

## Hardware

- Raspberry Pi 3B+
- SK9822 LED strip (1m / 60 LEDs)
- GPIO breakout board
- Zoom H6 (USB audio interface for audio-reactive modes)

## Features

- 8–12 built-in animation sequences
- Speed and brightness controls
- Audio-reactive modes (VU meter, spectrum, beat pulse, frequency color)
- Web UI accessible from any browser on the local network

## Installation

```bash
git clone https://github.com/yourusername/led-server.git
cd led-server
chmod +x install.sh
./install.sh
```

## Usage

After installation the server starts automatically on boot. Open a browser and navigate to:
http://<pi-ip-address>:5000

## Development

Active development happens on the `dev` branch. The `main` branch represents stable, deployed code only.