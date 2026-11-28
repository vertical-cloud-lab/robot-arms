# Environment used for the install steps (sourced, not run)
export PATH=$HOME/.local/bin:$PATH
export C=$HOME/capx UV_CACHE_DIR=$HOME/capx/uv-cache UV_LINK_MODE=copy
export UV_PYTHON_INSTALL_DIR=$HOME/capx/python   # keep uv's managed CPython under $HOME/capx
export PIP_TIMEOUT=600 PIP_RETRIES=2 UV_HTTP_TIMEOUT=600
export X=/tmp/ext/ml-amp/external/cap-x
