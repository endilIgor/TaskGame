#!/usr/bin/env bash
set -euo pipefail
umask 077

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_mysql.sh backups/mysql/taskgame-YYYYMMDD-HHMMSS.sql.gz" >&2
  exit 2
fi

: "${MYSQL_HOST:=db}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_DATABASE:=taskgame}"
: "${MYSQL_USER:=taskgame}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"

CLIENT_OPTIONS="$(mktemp "${TMPDIR:-/tmp}/taskgame-mysql.XXXXXX.cnf")"
trap 'rm -f "$CLIENT_OPTIONS"' EXIT

mysql_option_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  printf '%s' "$value"
}

printf '[client]\npassword="%s"\n' "$(mysql_option_escape "$MYSQL_PASSWORD")" > "$CLIENT_OPTIONS"

gzip -dc "$1" | mysql \
  --defaults-extra-file="$CLIENT_OPTIONS" \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  "$MYSQL_DATABASE"
