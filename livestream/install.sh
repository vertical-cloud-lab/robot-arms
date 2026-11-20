#!/bin/bash
# Install or update the livestream on a Pi. Run as the login user from a copy
# of this directory: ./install.sh  (asks for sudo once, for the systemd units).
# Needs settings here or in ~/picam-stream already (see my_secrets_example.py):
# my_secrets.py for one camera (picam-stream.service), or my_secrets_<name>.py
# for each camera on a Pi with several (picam-stream@<name>.service).
set -euo pipefail
shopt -s nullglob
SRC=$(cd "$(dirname "$0")" && pwd)
DEST=$HOME/picam-stream
settings() { for f in "$1"/my_secrets.py "$1"/my_secrets_*.py; do
  [ "$(basename "$f")" = my_secrets_example.py ] || echo "$f"; done; }
[ -n "$(settings "$SRC")$(settings "$DEST")" ] || { echo "my_secrets.py missing"; exit 1; }
command -v ffmpeg >/dev/null || sudo apt-get install -y --no-install-recommends ffmpeg
mkdir -p "$DEST"
install -m 644 "$SRC"/device.py "$SRC"/requirements.txt "$SRC"/requirements-deface.txt \
  "$SRC"/face_detection_yunet_2023mar.onnx "$DEST"/
for f in $(settings "$SRC"); do install -m 600 "$f" "$DEST/"; done
[ -x "$DEST/venv/bin/python" ] || python3 -m venv --system-site-packages "$DEST/venv"
"$DEST/venv/bin/pip" install -q -r "$DEST/requirements.txt"
"$DEST/venv/bin/pip" install -q --no-deps --require-hashes -r "$DEST/requirements-deface.txt"
for unit in picam-stream.service picam-stream@.service; do
  sed "s#@USER@#$(id -un)#; s#@HOME@#$HOME#g" "$SRC/$unit" |
    sudo tee "/etc/systemd/system/$unit" >/dev/null
done
sudo systemctl daemon-reload
echo "Installed. Start with: sudo systemctl enable --now picam-stream.service"
echo "  (or picam-stream@<name>.service for each my_secrets_<name>.py)"
