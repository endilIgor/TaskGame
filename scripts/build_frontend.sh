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

PREBUILT_DIR="frontend/prebuilt"
DIST_DIR="frontend/dist"

if [ ! -f "$PREBUILT_DIR/app.js" ]; then
  echo "TypeScript compiler not found and prebuilt frontend modules are missing." >&2
  exit 127
fi

rm -f "$DIST_DIR"/*.js "$DIST_DIR"/*.js.map
cp "$PREBUILT_DIR"/*.js "$DIST_DIR"/
sed -i '/^\/\/# sourceMappingURL=/d' "$DIST_DIR"/*.js
