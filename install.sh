#!/usr/bin/env bash
# install.sh — run once on the Raspberry Pi to set up the LED server.
# Must be run from the repository root.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/venv"
SERVICE_NAME="led-server"
SYSTEMD_DIR="/etc/systemd/system"
CURRENT_USER="${SUDO_USER:-$(whoami)}"

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
echo "==> Updating package lists..."
sudo apt update

echo "==> Installing system dependencies..."
sudo apt install -y python3-full python3-venv git portaudio19-dev python3-dev

# ---------------------------------------------------------------------------
# 2. Enable SPI (required for the APA102/SK9822 strip)
# ---------------------------------------------------------------------------
echo "==> Enabling SPI interface..."
sudo raspi-config nonint do_spi 0

# ---------------------------------------------------------------------------
# 3. Python virtual environment
#    --system-site-packages lets the venv inherit any system-installed
#    packages (e.g. numpy, RPi.GPIO) so we don't rebuild them from source.
# ---------------------------------------------------------------------------
echo "==> Creating Python virtual environment..."
python3 -m venv --system-site-packages "$VENV_DIR"

echo "==> Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

# ---------------------------------------------------------------------------
# 4. systemd service
#    Patch the template placeholders with real paths, then install.
# ---------------------------------------------------------------------------
echo "==> Installing systemd service..."
sed \
  -e "s|__VENV_PYTHON__|$VENV_DIR/bin/python|g" \
  -e "s|__APP_DIR__|$REPO_DIR|g" \
  -e "s|__USER__|$CURRENT_USER|g" \
  "$REPO_DIR/led-server.service" \
  | sudo tee "$SYSTEMD_DIR/$SERVICE_NAME.service" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# ---------------------------------------------------------------------------
# 5. Shell alias
# ---------------------------------------------------------------------------
echo "==> Adding shell aliases to ~/.bashrc..."
grep -q "led-deploy" ~/.bashrc 2>/dev/null || printf "%s\n" "alias led-deploy='cd $REPO_DIR && git pull && sudo find . -path ./venv -prune -o -name __pycache__ -type d -exec rm -rf {} + ; sudo systemctl restart led-server'" >> ~/.bashrc
grep -q "led-startup" ~/.bashrc 2>/dev/null || printf '%s\n' 'led-startup() { echo "Hardware Startup Checklist"; echo "1. H6 - Power on, Interface mode, Use battery"; echo "2. Pi - Power on, wait 30s"; echo "3. LED PSU - Power on last"; }' >> ~/.bashrc
echo "    Run 'source ~/.bashrc' or open a new terminal to activate."

# ---------------------------------------------------------------------------
# 6. Done
# ---------------------------------------------------------------------------
echo ""
echo "==> Installation complete."
echo "    Status:  sudo systemctl status $SERVICE_NAME"
echo "    Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "    Web UI:  http://$(hostname -I | awk '{print $1}'):5000"
