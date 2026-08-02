#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/restore_mysql.sh backups/mysql/taskgame-YYYYMMDD-HHMMSS.sql.gz" >&2
  exit 2
fi

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

gzip -dc "$1" | mysql \
  --host="$MYSQL_HOST" \
  --port="$MYSQL_PORT" \
  --user="$MYSQL_USER" \
  --password="$MYSQL_PASSWORD" \
  "$MYSQL_DATABASE"
