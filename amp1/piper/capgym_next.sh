#!/usr/bin/env bash
# capgym_next.sh TASK EPISODE [PORT]: queue the next CaP-Gym episode on the running capgym stack
# (from capgym_up.sh) with a fresh kernel bridge, frame recorder and episode directory.
set -euo pipefail
TASK=$1; K=$2; PORT=${3:-8768}
PY=/tmp/ext/ml-amp/.venv/bin/python
RUN=/tmp/amp-run/capgym_cube_lifting
URL=http://127.0.0.1:$PORT
EPDIR=/tmp/amp-episodes/capgym_${TASK}-ep${K}
FR=$RUN/frames_${TASK}_ep${K}
mkdir -p "$EPDIR"
for p in kernel recorder; do [ -f "$RUN/$p.pid" ] && kill "$(cat $RUN/$p.pid)" 2>/dev/null || true; done
export PYTHONPATH=/tmp/ext/ml-amp/src:/tmp/amp-piper
curl -fs -X POST -H 'content-type: application/json' -d "{\"task\": \"$TASK\", \"episode\": $K}" "$URL/api/tasks/select"; echo
for i in $(seq 1 240); do
  st=$(curl -fs "$URL/api/state" | $PY -c "import json,sys; s=json.load(sys.stdin); print(s.get('mode'), s.get('episode'), s.get('task'))")
  case "$st" in "awaiting_plan $K $TASK") break;; esac
  $PY -c "import time; time.sleep(1)"
done
echo "state: $st"
nohup $PY /tmp/amp-piper/kernel_bridge.py serve "$EPDIR" "$URL" > "$RUN/kernel_${TASK}_ep${K}.log" 2>&1 &
echo $! > "$RUN/kernel.pid"
nohup $PY /tmp/amp-piper/recorder.py "$URL" robot0_robotview "$FR" > "$RUN/recorder_${TASK}.log" 2>&1 &
echo $! > "$RUN/recorder.pid"
for i in $(seq 1 60); do grep -q "kernel ready" "$RUN/kernel_${TASK}_ep${K}.log" 2>/dev/null && break; $PY -c "import time; time.sleep(0.5)"; done
cat > "$EPDIR/py" <<PYEOF
#!/usr/bin/env bash
exec $PY /tmp/amp-piper/kernel_bridge.py run "$EPDIR" "\$@"
PYEOF
cat > "$EPDIR/finish_episode" <<PYEOF
#!/usr/bin/env bash
exec $PY /tmp/amp-piper/kernel_bridge.py finish "$EPDIR" "\$@"
PYEOF
chmod +x "$EPDIR/py" "$EPDIR/finish_episode"
echo "{\"frames\": \"$FR\", \"results\": \"$RUN/slot/results/$TASK\", \"fps\": 20}" > "$EPDIR/.run.json"
$PY /tmp/amp-piper/compose_prompt.py "$EPDIR" 45
echo "episode dir: $EPDIR"
