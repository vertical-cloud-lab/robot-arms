# Environment for AMP's CaP-Gym LIBERO-PRO family (capgym_libero) on a CPU-only host with Mesa EGL
# (llvmpipe): env.sh with the LIBERO-PRO venv, its LIBERO config and its own CaP-X checkout copy.
# Source it, then start the client with the CaP-X LIBERO-PRO venv's python:
#
#   source /tmp/capgym_test/env_libero.sh [SLOT_DIR]  # SLOT_DIR defaults to /tmp/capgym_test/slot_libero
#   python -m amp.robots.capgym --server http://127.0.0.1:PORT --benchmark --adapter official \
#       --output-dir "$CAPGYM_RESULTS_DIR" --cameras droid --info standard --episodes-per-task 1 \
#       --policy-label "AMP Agent" --max-steps 0 --seed 0 --task-set capgym_libero
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
_capx_slot=${1:-${CAPGYM_SLOT_DIR:-/tmp/capgym_test/slot_libero}}

# Interpreters: the CaP-X LIBERO-PRO venv (CPython 3.12) first, so `python` is that venv; uv too.
export PATH="$_capx_home/capx/venv-libero/bin:$_capx_home/.local/bin:$PATH"

# docs/capgym.md section 1 ("for every run") -- LIBERO-PRO family only. AMP_CAPX_ROOT is a copy of the
# pinned checkout (libero_setup.sh), so building this venv never touched the robosuite venv's.
export AMP_CAPX_ROOT=${AMP_CAPX_ROOT_LIBERO:-/tmp/ext/cap-x-libero}
export AMP_CAPX_LIBERO_PYTHON=$_capx_home/capx/venv-libero/bin/python
export LIBERO_CONFIG_PATH=$_capx_home/capx/libero

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
