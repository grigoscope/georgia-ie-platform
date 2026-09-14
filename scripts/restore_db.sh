#!/usr/bin/env bash

set -euo pipefail

POSTGRES_DB="${POSTGRES_DB:-georgia_ie}"
POSTGRES_USER="${POSTGRES_USER:-georgia_ie}"

if [ "$#" -ne 1 ]; then
    echo "Usage: ./scripts/restore_db.sh path/to/backup.dump"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

docker compose exec -T postgres \
    pg_restore \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    < "$BACKUP_FILE"

echo "Restore completed from: $BACKUP_FILE"