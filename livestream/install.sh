#!/bin/bash
# Install or update the livestream on a Pi. Run as the login user from a copy
# of this directory: ./install.sh  (asks for sudo once, for the systemd unit).
# Needs my_secrets.py here already (see my_secrets_example.py).
set -euo pipefail
SRC=$(cd "$(dirname "$0")" && pwd)
DEST=$HOME/picam-stream
[ -f "$SRC/my_secrets.py" ] || [ -f "$DEST/my_secrets.py" ] || { echo "my_secrets.py missing"; exit 1; }
command -v ffmpeg >/dev/null || sudo apt-get install -y --no-install-recommends ffmpeg
mkdir -p "$DEST"
install -m 644 "$SRC"/device.py "$SRC"/requirements.txt "$SRC"/face_detection_yunet_2023mar.onnx "$DEST"/
[ -f "$SRC/my_secrets.py" ] && install -m 600 "$SRC/my_secrets.py" "$DEST/"
[ -x "$DEST/venv/bin/python" ] || python3 -m venv --system-site-packages "$DEST/venv"
"$DEST/venv/bin/pip" install -q -r "$DEST/requirements.txt"
sed "s#@USER@#$(id -un)#; s#@HOME@#$HOME#g" "$SRC/picam-stream.service" |
  sudo tee /etc/systemd/system/picam-stream.service >/dev/null
sudo systemctl daemon-reload
echo "Installed. Start with: sudo systemctl enable --now picam-stream.service"
