#!/usr/bin/env bash
# Grab one frame from each PiPER table camera without disturbing the livestreams.
#
#   scripts/table_camera_frames.sh [OUTDIR]        (default: .)
#
# Each table Pi streams through systemd (#61): eufi and mpzy run one
# picam-stream.service, and 76zj runs one picam-stream@<name>.service per gripper
# camera (wide, hq). A stream holds its camera, so for every running stream this
# copies the frame it last sent instead: /tmp/picam-stream-latest.jpg, or
# /tmp/picam-stream-<name>-latest.jpg for an instance, faces already pixelated,
# refreshed every 30 s. It never opens a camera on a Pi where any stream is
# running or starting, never stops or restarts a service and never reboots a
# Pi. On a Pi with no stream it takes one rpicam-still per camera, which is NOT
# face-blurred: blur people before committing a frame.
#
# Needs the session's tailnet and the *_USERNAME / *_HOSTNAME variables from
# CLAUDE.md. Prints Pi IDs only, never hostnames.
set -uo pipefail
out=${1:-.}
mkdir -p "$out"
ssh_pi() { ssh -n -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 "$@"; }

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
  # Every stream unit systemd has loaded, as "unit active-state sub-state".
  units=$(ssh_pi "$dest" "systemctl list-units --all --type=service --no-legend --plain 'picam-stream.service' 'picam-stream@*.service'" | awk '{print $1, $3, $4}')
  streaming=0
  running=0
  while read -r unit active sub; do
    [ -n "$unit" ] || continue
    case $unit in
      picam-stream.service) frame=/tmp/picam-stream-latest.jpg; name=stream ;;
      picam-stream@*.service)
        inst=${unit#picam-stream@}
        inst=${inst%.service}
        if ! [[ $inst =~ ^[A-Za-z0-9_]+$ ]]; then
          echo "$id: skipped unit with an unexpected name"
          streaming=1
          continue
        fi
        frame=/tmp/picam-stream-$inst-latest.jpg
        name=${inst}_stream ;;
      *) continue ;;
    esac
    case $active in active | activating | reloading | deactivating) streaming=1 ;; esac
    if [ "$sub" != running ]; then
      [ "$active" = inactive ] || echo "$id: $unit is $active ($sub); no frame copied"
      continue
    fi
    running=$((running + 1))
    age=$(ssh_pi "$dest" "f=$frame; [ -f \$f ] && echo \$(( \$(date +%s) - \$(stat -c %Y \$f) ))")
    if [ -z "$age" ]; then
      echo "$id: $unit running but no saved frame yet; try again in 30 s"
      continue
    fi
    ssh_pi "$dest" "cat $frame" > "$out/${id}_${name}.jpg"
    echo "$id: $unit running; copied the frame it sent ${age} s ago to $out/${id}_${name}.jpg"
  done <<< "$units"
  if [ "$streaming" -eq 1 ]; then
    # Sensors the kernel found, counted without starting libcamera.
    sensors=$(ssh_pi "$dest" 'ls -d /sys/bus/i2c/drivers/imx*/*-00* 2>/dev/null | wc -l')
    if [ "${sensors:-0}" -gt "$running" ]; then
      echo "$id: $sensors sensors attached, $running streaming; the others were not opened, since a stream runs on this Pi"
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
