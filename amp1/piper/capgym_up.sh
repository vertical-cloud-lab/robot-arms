#!/usr/bin/env bash
# capgym_up.sh TASK PORT [EPISODE]: AMP robot server (amp1_basic) + CaP-Gym robosuite link client
# (CaP-X's own env through AMP's official adapter) + kernel bridge + frame recorder, for one episode.
set -euo pipefail
TASK=$1; PORT=$2; K=${3:-0}; TASK_SET=${4:-capgym_robosuite_cube}; CAM=${5:-robot0_robotview}
PY=/tmp/ext/ml-amp/.venv/bin/python
RUN=/tmp/amp-run/capgym_$TASK
EPDIR=/tmp/amp-episodes/capgym_${TASK}-ep${K}
URL=http://127.0.0.1:$PORT
mkdir -p "$RUN" "$EPDIR"
export PYTHONPATH=/tmp/ext/ml-amp/src:/tmp/amp-piper
$PY - "$RUN" "$PORT" <<'EOF'
import json, sys
from amp.eval.robolab_slot import server_config
run, port = sys.argv[1], int(sys.argv[2])
cfg = server_config("amp1_basic", port=port, state_dir=f"{run}/state", results_dir=f"{run}/results")
open(f"{run}/server.json", "w").write(json.dumps(cfg, indent=1))
EOF
setsid $PY -m amp.robot_server --config "$RUN/server.json" > "$RUN/server.log" 2>&1 &
echo $! > "$RUN/server.pid"
for i in $(seq 1 60); do curl -fs "$URL/api/state" >/dev/null 2>&1 && break; $PY -c "import time; time.sleep(0.5)"; done
setsid bash -c "source /tmp/capgym_test/env.sh '$RUN/slot' && cd \"\$CAPGYM_SLOT_DIR\" && exec python -m amp.robots.capgym --server '$URL' --adapter official --benchmark --output-dir \"\$CAPGYM_RESULTS_DIR\" --task-set $TASK_SET --seed 0" > "$RUN/link.log" 2>&1 &
echo $! > "$RUN/link.pid"
for i in $(seq 1 120); do grep -q "catalog:" "$RUN/link.log" 2>/dev/null && break; $PY -c "import time; time.sleep(1)"; done
tail -3 "$RUN/link.log"
curl -fs -X POST -H 'content-type: application/json' -d "{\"task\": \"$TASK\", \"episode\": $K}" "$URL/api/tasks/select"; echo
for i in $(seq 1 180); do
  st=$(curl -fs "$URL/api/state" | $PY -c "import json,sys; s=json.load(sys.stdin); print(s.get('mode'), s.get('episode'))")
  case "$st" in awaiting_plan*) break;; esac
  $PY -c "import time; time.sleep(1)"
done
echo "state: $st"
nohup $PY /tmp/amp-piper/kernel_bridge.py serve "$EPDIR" "$URL" > "$RUN/kernel.log" 2>&1 &
echo $! > "$RUN/kernel.pid"
nohup $PY /tmp/amp-piper/recorder.py "$URL" "$CAM" "$RUN/frames" > "$RUN/recorder.log" 2>&1 &
echo $! > "$RUN/recorder.pid"
for i in $(seq 1 60); do grep -q "kernel ready" "$RUN/kernel.log" 2>/dev/null && break; $PY -c "import time; time.sleep(0.5)"; done
cat "$RUN/kernel.log"
cat > "$EPDIR/py" <<PYEOF
#!/usr/bin/env bash
exec $PY /tmp/amp-piper/kernel_bridge.py run "$EPDIR" "\$@"
PYEOF
cat > "$EPDIR/finish_episode" <<PYEOF
#!/usr/bin/env bash
exec $PY /tmp/amp-piper/kernel_bridge.py finish "$EPDIR" "\$@"
PYEOF
chmod +x "$EPDIR/py" "$EPDIR/finish_episode"
echo "episode dir: $EPDIR"
