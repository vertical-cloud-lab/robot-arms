#!/usr/bin/env bash
# episode_up.sh TASK PORT [EPISODE]: AMP robot server + PiPER link client + kernel bridge for one episode
set -euo pipefail
TASK=$1; PORT=$2; K=${3:-0}
PY=/tmp/ext/ml-amp/.venv/bin/python
export PIPER_RUN_DIR=/tmp/amp-run/$TASK PIPER_SERVER_PORT=$PORT PIPER_FRAMES_DIR=/tmp/amp-run/$TASK/frames
# the task (a task may widen the perception box) and a model directory of its own, so stacks for
# different tasks can run side by side
export PIPER_TASK=$TASK PIPER_SIM_DIR=/tmp/amp-run/$TASK/model
export PYTHONPATH=/tmp/ext/ml-amp/src:/tmp/amp-piper MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
EPDIR=/tmp/amp-episodes/${TASK}-ep${K}
mkdir -p "$EPDIR"
$PY /tmp/amp-piper/stack.py up
$PY /tmp/amp-piper/stack.py select "$TASK" "$K"
nohup $PY /tmp/amp-piper/kernel_bridge.py serve "$EPDIR" "http://127.0.0.1:$PORT" > "/tmp/amp-run/$TASK/kernel.log" 2>&1 &
echo $! > "/tmp/amp-run/$TASK/kernel.pid"
for i in $(seq 1 60); do grep -q "kernel ready" "/tmp/amp-run/$TASK/kernel.log" 2>/dev/null && break; $PY -c "import time; time.sleep(0.5)"; done
cat "/tmp/amp-run/$TASK/kernel.log"
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
