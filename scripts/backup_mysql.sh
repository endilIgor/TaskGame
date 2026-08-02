#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${MYSQL_HOST:=db}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_DATABASE:=taskgame}"
: "${MYSQL_USER:=taskgame}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"

python -m backend.app.services.mysql_dump backup
