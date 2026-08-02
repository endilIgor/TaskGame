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

python -m backend.app.services.mysql_dump restore "$1"
