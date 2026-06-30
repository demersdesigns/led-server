#!/usr/bin/env bash
# fix-bashrc.sh — run on the Pi to clean up broken .bashrc alias lines
# Usage: bash fix-bashrc.sh

set -euo pipefail

BASHRC="$HOME/.bashrc"

echo "==> Backing up $BASHRC to $BASHRC.bak"
cp "$BASHRC" "$BASHRC.bak"

echo "==> Removing broken led-* lines..."
# Remove any line mentioning these aliases or their fragments
sed -i '/led-deploy/d'   "$BASHRC"
sed -i '/led-startup/d'  "$BASHRC"
sed -i '/^latest()/d'    "$BASHRC"
# Remove continuation lines from the broken latest() function
sed -i '/git pull && find/d' "$BASHRC"
sed -i '/systemctl restart led-server/d' "$BASHRC"
# Remove dangling fragments and multiline led-startup content
sed -i '/Hardware Startup/d'  "$BASHRC"
sed -i '/Zoom H6/d'           "$BASHRC"
sed -i '/LED PSU/d'           "$BASHRC"
sed -i '/Interface mode/d'    "$BASHRC"
sed -i '/Power on/d'          "$BASHRC"
sed -i '/^ *-rf {} /d'        "$BASHRC"
sed -i "/^  sudo systemctl/d" "$BASHRC"

echo "==> Adding clean led-deploy alias..."
printf '%s\n' "alias led-deploy='cd ~/led-server && git pull && sudo find . -path ./venv -prune -o -name __pycache__ -type d -exec rm -rf {} + ; sudo systemctl restart led-server'" >> "$BASHRC"

echo "==> Adding clean led-startup function..."
printf '%s\n' 'led-startup() { echo "Hardware Startup Checklist"; echo "1. H6 - Power on, Interface mode, Use battery"; echo "2. Pi - Power on, wait 30s"; echo "3. LED PSU - Power on last"; }' >> "$BASHRC"

echo "==> Done. Run:  source ~/.bashrc"
