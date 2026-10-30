#!/usr/bin/env bash
# User-owned environment; no sudo, shell-profile changes, or Apple credential operations.
set -euo pipefail
if [[ "$(uname -s)" != Linux ]]; then
  echo 'This installer targets Linux; use python -m pip install -e . on other hosts.' >&2
  exit 1
fi
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
python_bin=${PYTHON_BIN:-python3}
"$python_bin" -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"'
venv_path=${REMOTE_IOS_VENV:-"$repo_dir/.venv"}
"$python_bin" -m venv "$venv_path"
"$venv_path/bin/python" -m pip install -e "$repo_dir[device,mcp]"
"$venv_path/bin/remote-ios" doctor
printf 'Activate with: source %q/bin/activate\n' "$venv_path"
