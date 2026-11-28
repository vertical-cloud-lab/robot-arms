#!/usr/bin/env bash
# episode_up.sh TASK PORT [EPISODE]: AMP robot server + PiPER link client + kernel bridge for one episode
# PIPER_RUN_NAME names the stack's directory under /tmp/amp-run (default TASK); give each episode
# its own to run two episodes of one task side by side
set -euo pipefail
TASK=$1; PORT=$2; K=${3:-0}
PY=/tmp/ext/ml-amp/.venv/bin/python
RUN=/tmp/amp-run/${PIPER_RUN_NAME:-$TASK}
export PIPER_RUN_DIR=$RUN PIPER_SERVER_PORT=$PORT PIPER_FRAMES_DIR=$RUN/frames
# the task (a task may widen the perception box) and a model directory of its own, so stacks for
# different tasks can run side by side
export PIPER_TASK=$TASK PIPER_SIM_DIR=$RUN/model
export PYTHONPATH=/tmp/ext/ml-amp/src:/tmp/amp-piper MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
EPDIR=/tmp/amp-episodes/${TASK}-ep${K}
mkdir -p "$EPDIR"
$PY /tmp/amp-piper/stack.py up
$PY /tmp/amp-piper/stack.py select "$TASK" "$K"
nohup $PY /tmp/amp-piper/kernel_bridge.py serve "$EPDIR" "http://127.0.0.1:$PORT" > "$RUN/kernel.log" 2>&1 &
echo $! > "$RUN/kernel.pid"
for i in $(seq 1 60); do grep -q "kernel ready" "$RUN/kernel.log" 2>/dev/null && break; $PY -c "import time; time.sleep(0.5)"; done
cat "$RUN/kernel.log"
# where summarize.py and collect.py find the episode's frames, the simulator's truth file and results
echo "{\"frames\": \"$RUN/frames/${TASK}_ep${K}\", \"truth\": \"$RUN/frames/${TASK}_truth.json\", \"results\": \"$RUN/bench\"}" > "$EPDIR/.run.json"
# the agent's python(code) tool
cat > "$EPDIR/py" <<PYEOF
#!/usr/bin/env bash
# python(code): run stdin as one cell in the episode's persistent kernel; --timeout S optional
exec $PY /tmp/amp-piper/kernel_bridge.py run "$EPDIR" "\$@"
PYEOF
cat > "$EPDIR/finish_episode" <<PYEOF
#!/usr/bin/env bash
# finish_episode(reason): end the episode now, scored as it stands
exec $PY /tmp/amp-piper/kernel_bridge.py finish "$EPDIR" "\$@"
PYEOF
chmod +x "$EPDIR/py" "$EPDIR/finish_episode"
echo "episode dir: $EPDIR"
