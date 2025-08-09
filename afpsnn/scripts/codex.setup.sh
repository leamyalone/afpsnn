#!/usr/bin/env bash
set -euo pipefail

# Idempotent, non-interactive setup for ChatGPT/Codex sandboxes (CPU by default).
# - Creates venv if missing
# - Installs requirements
# - Attempts a kernel build if CUDA toolchain exists; otherwise skips gracefully

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate

pip install -r requirements.txt -q || true

# Detect CUDA toolchain
has_nvcc=false
if command -v nvcc >/dev/null 2>&1; then
  has_nvcc=true
fi

if $has_nvcc; then
  mkdir -p build
  pushd build >/dev/null
  cmake ../src >/dev/null || true
  cmake --build . >/dev/null || true
  popd >/dev/null
  echo "[setup] CUDA toolchain detected; attempted kernel build."
else
  echo "[setup] No CUDA toolchain detected; proceeding with CPU-only smoke."
fi

echo "[setup] Done."
