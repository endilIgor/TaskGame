#!/usr/bin/env bash
set -euo pipefail

run_tsc() {
  if "$@" --version | grep -q 'Version 6\.'; then
    "$@" --ignoreDeprecations 6.0 --project tsconfig.json
    return
  fi

  "$@" --project tsconfig.json
}

if [ -n "${TSC_BIN:-}" ]; then
  run_tsc "$TSC_BIN"
  exit 0
fi

if command -v tsc >/dev/null 2>&1; then
  run_tsc tsc
  exit 0
fi

LOCAL_TSC_BIN="/home/nagi/.hermes/hermes-agent/node_modules/typescript/bin/tsc"
if [ -f "$LOCAL_TSC_BIN" ] && command -v node >/dev/null 2>&1; then
  run_tsc node "$LOCAL_TSC_BIN"
  exit 0
fi

echo "TypeScript compiler not found. Set TSC_BIN, install 'tsc', or provide $LOCAL_TSC_BIN with node." >&2
exit 127
