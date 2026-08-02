#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${MYSQL_HOST:=db}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_DATABASE:=taskgame}"
: "${MYSQL_USER:=taskgame}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"

BACKUP_ROOT="${BACKUP_DIR:-./backups}/mysql"
mkdir -p "$BACKUP_ROOT"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_ROOT/taskgame-$STAMP.sql.gz"
if [ -e "$OUT" ]; then
  echo "Backup already exists: $OUT" >&2
  exit 1
fi

CLIENT_OPTIONS="$(mktemp "${TMPDIR:-/tmp}/taskgame-mysql.XXXXXX.cnf")"
PARTIAL="$(mktemp "$BACKUP_ROOT/.taskgame-$STAMP.XXXXXX.sql.gz")"

cleanup() {
  rm -f "$CLIENT_OPTIONS"
  if [ -n "$PARTIAL" ]; then
    rm -f "$PARTIAL"
  fi
}
trap cleanup EXIT

mysql_option_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  printf '%s' "$value"
}

printf '[client]\npassword="%s"\n' "$(mysql_option_escape "$MYSQL_PASSWORD")" > "$CLIENT_OPTIONS"

mysqldump \
  --defaults-extra-file="$CLIENT_OPTIONS" \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  "$MYSQL_DATABASE" | gzip > "$PARTIAL"

mv "$PARTIAL" "$OUT"
PARTIAL=""

echo "$OUT"
