#!/usr/bin/env bash
set -euo pipefail

if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

: "${MYSQL_HOST:=db}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_DATABASE:=taskgame}"
: "${MYSQL_USER:=taskgame}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"

BACKUP_ROOT="${BACKUP_DIR:-./backups}/mysql"
mkdir -p "$BACKUP_ROOT"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_ROOT/taskgame-$STAMP.sql.gz"

mysqldump \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  --password="$MYSQL_PASSWORD" \
  "$MYSQL_DATABASE" | gzip > "$OUT"

echo "$OUT"
