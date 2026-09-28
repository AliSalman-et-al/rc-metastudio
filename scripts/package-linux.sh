#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"

if [ "$(uname -s)" != "Linux" ] || [ "$(uname -m)" != "x86_64" ]; then
  echo "Linux packaging requires an x86_64 host." >&2
  exit 1
fi
if [ ! -r /etc/os-release ]; then
  echo "Linux packaging requires Ubuntu 24.04 (Noble)." >&2
  exit 1
fi
. /etc/os-release
if { [ "${ID:-}" != "ubuntu" ] || [ "${VERSION_ID:-}" != "24.04" ]; } &&
   [ "${UBUNTU_CODENAME:-}" != "noble" ]; then
  echo "Linux packaging requires Ubuntu 24.04 (Noble) or a Noble-based distribution." >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "Linux packaging requires uv. Install it from https://docs.astral.sh/uv/." >&2
  exit 1
fi

cd "$repo_root"
uv python install 3.11.9
RPY2_CFFI_MODE=ABI uv sync --locked
bash "$repo_root/scripts/build-linux-package.sh" \
  --python-exe "$repo_root/.venv/bin/python"
