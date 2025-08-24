#!/usr/bin/env bash
set -euo pipefail

echo "[qa] compiling: 1.1.0_birha.py"
python -m py_compile 1.1.0_birha.py
python - <<'PY'
import sys, platform
print(f"[qa] python:", sys.version.replace("\n"," "))
print(f"[qa] platform:", platform.platform())
PY

echo "[qa] lint: probing optional linters"
if command -v ruff >/dev/null 2>&1; then
  echo "[qa] ruff found → running 'ruff check 1.1.0_birha.py' (non-fatal)"
  if ruff check 1.1.0_birha.py; then
    echo "[qa] ruff: clean"
  else
    echo "[qa] ruff: issues found (tolerated)"
  fi
elif command -v flake8 >/dev/null 2>&1; then
  echo "[qa] flake8 found → running 'flake8 1.1.0_birha.py' (non-fatal)"
  if flake8 1.1.0_birha.py; then
    echo "[qa] flake8: clean"
  else
    echo "[qa] flake8: issues found (tolerated)"
  fi
else
  echo "[qa] no linter found → skipping lint (ok)"
fi

echo "[qa] OK: basic QA checks passed."
