#!/usr/bin/env bash
set -euo pipefail

if [ -x "frontend/node_modules/.bin/vite" ]; then
  npm --prefix frontend run build
  exit 0
fi

if command -v npm >/dev/null 2>&1 && [ -f "frontend/package-lock.json" ]; then
  npm --prefix frontend ci
  npm --prefix frontend run build
  exit 0
fi

if [ -f "frontend/dist/index.html" ] && find frontend/dist/assets -type f -name '*.js' | grep -q .; then
  exit 0
fi

echo "React frontend build is missing. Run npm --prefix frontend ci && npm --prefix frontend run build." >&2
exit 127
