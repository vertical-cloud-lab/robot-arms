# Environment for AMP's CaP-Gym robosuite family (capgym_robosuite_cube, ...) on a CPU-only host
# with Mesa EGL (llvmpipe). Source it, then start the client with the CaP-X robosuite venv's python:
#
#   source /tmp/capgym_test/env.sh [SLOT_DIR]        # SLOT_DIR defaults to /tmp/capgym_test/slot
#   python -m amp.robots.capgym --server http://127.0.0.1:PORT --benchmark --adapter official \
#       --output-dir "$CAPGYM_RESULTS_DIR" --cameras droid --info standard --episodes-per-task 1 \
#       --policy-label "AMP Agent" --max-steps 0 --seed 0 --task-set capgym_robosuite_cube
#
# It reproduces what AMP's launcher gives the client process: CapgymSlot.client_env()
# (src/amp/eval/capgym_slot.py) = this environment minus CapgymBackend.env_unset(), plus
# PYTHONPATH/PYTHONUNBUFFERED, plus CapgymBackend.env() (src/amp/robots/capgym/backend.py), plus
# MUJOCO_EGL_DEVICE_ID and CUDA_VISIBLE_DEVICES="" for an EGL family. The one difference: the
# launcher picks the EGL device from the NVIDIA GPU it schedules on; here the only EGL device is
# Mesa's, index 0.
#
# By default it also sets the per-slot sandbox the backend sets (HOME, TMPDIR, XDG_*, ... under
# $SLOT_DIR/sandbox, results in $SLOT_DIR/results), so sourcing it changes HOME for the rest of
# that shell. CAPGYM_SANDBOX=0 skips that part.

_capx_home=/home/runner
_capx_slot=${1:-${CAPGYM_SLOT_DIR:-/tmp/capgym_test/slot}}

# Interpreters: the CaP-X robosuite venv (CPython 3.10) first, so `python` is that venv; uv too.
export PATH="$_capx_home/capx/venv-robosuite/bin:$_capx_home/.local/bin:$PATH"

# docs/capgym.md section 1 ("for every run") -- robosuite family only.
export AMP_CAPX_ROOT=/tmp/ext/ml-amp/external/cap-x
export AMP_CAPX_ROBOSUITE_PYTHON=$_capx_home/capx/venv-robosuite/bin/python

# CapgymSlot.client_env + CapgymBackend.env: AMP's src importable (nothing else), unbuffered,
# one BLAS/OpenMP thread.
export PYTHONPATH=/tmp/ext/ml-amp/src
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

# MuJoCo EGL family: offscreen EGL, no CUDA device. robosuite's EGL context falls back to
# CUDA_VISIBLE_DEVICES when MUJOCO_EGL_DEVICE_ID is unset, and int("") fails, so keep both.
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
export CUDA_VISIBLE_DEVICES=
export MUJOCO_EGL_DEVICE_ID=0

# CapgymBackend.env_unset for a MuJoCo family: ISAAC_ABSENT = ISAAC_*, CARB_*, EXP_PATH, LD_LIBRARY_PATH.
unset EXP_PATH LD_LIBRARY_PATH
for _v in $(compgen -e); do
  case "$_v" in ISAAC_*|CARB_*) unset "$_v" ;; esac
done

# The slot: results folder for --output-dir, and the backend's sandbox (sandbox.sandbox_env).
export CAPGYM_SLOT_DIR="$_capx_slot"
export CAPGYM_RESULTS_DIR="$_capx_slot/results"
mkdir -p "$CAPGYM_RESULTS_DIR"
if [ "${CAPGYM_SANDBOX:-1}" != 0 ]; then
  _sb="$_capx_slot/sandbox"
  export AMP_CAPGYM_SANDBOX="$_sb"
  export HOME="$_sb/home" TMPDIR="$_sb/tmp" XDG_RUNTIME_DIR="$_sb/run"
  export XDG_CACHE_HOME="$_sb/home/.cache" XDG_DATA_HOME="$_sb/home/.local/share"
  export XDG_CONFIG_HOME="$_sb/home/.config"
  export PYTHONDONTWRITEBYTECODE=1 NUMBA_CACHE_DIR="$_sb/numba"
  # what capgym_slot.prepare_sandbox makes (TMPDIR and XDG_RUNTIME_DIR are emptied again by the
  # client's own sandbox.install() at start-up)
  mkdir -p "$HOME" "$TMPDIR" "$XDG_RUNTIME_DIR" "$XDG_CACHE_HOME" "$XDG_DATA_HOME" \
           "$XDG_CONFIG_HOME" "$NUMBA_CACHE_DIR"
  chmod 700 "$XDG_RUNTIME_DIR"
  unset _sb
fi
unset _capx_home _capx_slot _v
