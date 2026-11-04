#!/usr/bin/env bash
# Grab one frame from each PiPER table camera without disturbing the livestreams.
#
#   scripts/table_camera_frames.sh [OUTDIR]        (default: .)
#
# On a Pi where picam-stream.service is running (eufi and mpzy, #61), the stream
# holds camera 0, so this copies the frame the stream last sent instead:
# /tmp/picam-stream-latest.jpg, faces already pixelated, refreshed every 30 s.
# It never opens a streaming Pi's camera, never stops or restarts a service and
# never reboots a Pi. On a Pi with no stream running it takes one rpicam-still
# per camera, which is NOT face-blurred: blur people before committing a frame.
#
# Needs the session's tailnet and the *_USERNAME / *_HOSTNAME variables from
# CLAUDE.md. Prints Pi IDs only, never hostnames.
set -uo pipefail
out=${1:-.}
mkdir -p "$out"
ssh_pi() { ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$@"; }

for entry in eufi:ARM_PI mpzy:CAM2_PI 76zj:CAM_PI; do
  id=${entry%%:*}
  user_var=${entry#*:}_USERNAME
  host_var=${entry#*:}_HOSTNAME
  if [ -z "${!user_var:-}" ] || [ -z "${!host_var:-}" ]; then
    echo "$id: $user_var or $host_var is not set; skipped"
    continue
  fi
  dest="${!user_var}@${!host_var}"
  if ! ssh_pi "$dest" true 2>/dev/null; then
    echo "$id: not reachable over Tailscale SSH"
    continue
  fi
  if ssh_pi "$dest" 'systemctl is-active --quiet picam-stream.service'; then
    # Sensors the kernel found, counted without starting libcamera.
    sensors=$(ssh_pi "$dest" 'ls -d /sys/bus/i2c/drivers/imx*/*-00* 2>/dev/null | wc -l')
    age=$(ssh_pi "$dest" 'f=/tmp/picam-stream-latest.jpg; [ -f $f ] && echo $(( $(date +%s) - $(stat -c %Y $f) ))')
    if [ -z "$age" ]; then
      echo "$id: stream running but no saved frame yet; try again in 30 s"
      continue
    fi
    ssh_pi "$dest" 'cat /tmp/picam-stream-latest.jpg' > "$out/${id}_stream.jpg"
    echo "$id: stream running; copied the frame it sent ${age} s ago to $out/${id}_stream.jpg"
    if [ "${sensors:-0}" -gt 1 ]; then
      echo "$id: $sensors sensors attached; the others were not opened, since the stream runs on this Pi"
    fi
    continue
  fi
  n=$(ssh_pi "$dest" 'rpicam-hello --list-cameras 2>&1 | grep -cE "^[0-9]+ : "')
  if [ "${n:-0}" -eq 0 ]; then
    echo "$id: no stream, and libcamera lists no camera"
    continue
  fi
  for ((i = 0; i < n; i++)); do
    f="$out/${id}_cam${i}.jpg"
    if ssh_pi "$dest" "t=\$(mktemp --suffix=.jpg); rpicam-still -n --camera $i -t 1500 -o \$t >/dev/null 2>&1 && cat \$t; rc=\$?; rm -f \$t; exit \$rc" > "$f"; then
      echo "$id: camera $i still saved to $f (not face-blurred)"
    else
      rm -f "$f"
      echo "$id: camera $i listed, but rpicam-still failed"
    fi
  done
done
