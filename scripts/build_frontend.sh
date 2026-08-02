#!/usr/bin/env bash
set -euo pipefail

if ! command -v tsc >/dev/null 2>&1; then
  echo "TypeScript compiler 'tsc' is required. In Docker it is installed from the OS package node-typescript." >&2
  exit 127
fi

tsc --project tsconfig.json
