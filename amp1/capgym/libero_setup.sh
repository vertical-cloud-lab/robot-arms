#!/usr/bin/env bash
# CaP-Gym LIBERO-PRO family on this runner: docs/capgym.md steps 2, 4, 5, in a copy of the
# CaP-X checkout (so the robosuite episode running from the original is not touched).
set -euo pipefail
export PATH=$HOME/.local/bin:$PATH PIP_TIMEOUT=600 PIP_RETRIES=2 UV_HTTP_TIMEOUT=600
export C=$HOME/capx UV_CACHE_DIR=$HOME/capx/uv-cache UV_LINK_MODE=copy UV_PYTHON_INSTALL_DIR=$HOME/capx/python
SRC=/tmp/ext/ml-amp/external/cap-x
X=/tmp/ext/cap-x-libero
[ -d $X ] || cp -a $SRC $X
git -C $X status --short | head -5
uv python install 3.12
uv venv $C/venv-libero --managed-python --python 3.12
(cd $X && VIRTUAL_ENV=$C/venv-libero uv sync --frozen --active --extra libero)
$C/venv-libero/bin/python -c "from huggingface_hub import snapshot_download as d; \
d('zhouxueyang/LIBERO-Pro', repo_type='dataset', \
revision='c86fc3b8293185a6f373677018ff3e37f8391602', local_dir='$C/hf/libero_data')"
(cd $C/hf/libero_data && tr -d '\r' < SHA256SUMS.txt | sha256sum -c --quiet -)
cd $X/capx/third_party/LIBERO-PRO
mv $C/hf/libero_data/bddl_files/* libero/libero/bddl_files/ || true
mv $C/hf/libero_data/init_files/* libero/libero/init_files/ || true
for t in bddl_files init_files; do for d in $C/hf/libero_data/$t/*; do
  [ ! -e "$d" ] || diff -r "$d" libero/libero/$t/$(basename $d); done; done
git diff --quiet HEAD && test -z "$(git ls-files --deleted)" && rm -rf $C/hf
cd -
mkdir -p $C/libero
B=$X/capx/third_party/LIBERO-PRO/libero/libero
printf 'assets: %s/assets\nbddl_files: %s/bddl_files\nbenchmark_root: %s\ndatasets: %s/../datasets\ninit_states: %s/init_files\n' \
  $B $B $B $B $B > $C/libero/config.yaml
echo LIBERO_SETUP_DONE
