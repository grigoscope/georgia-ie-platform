#!/usr/bin/env bash

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-backups}"
POSTGRES_DB="${POSTGRES_DB:-georgia_ie}"
POSTGRES_USER="${POSTGRES_USER:-georgia_ie}"

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_FILE="${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.dump"

docker compose exec -T postgres \
    pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -F c \
    > "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"