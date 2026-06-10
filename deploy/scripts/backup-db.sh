#!/bin/bash
# Backup PostgreSQL from Docker container
# Usage: ./deploy/scripts/backup-db.sh
# Cron:  0 3 * * * /path/to/project/deploy/scripts/backup-db.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BACKUP_DIR="${PROJECT_DIR}/backups"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -f "${PROJECT_DIR}/.env.prod" ]; then
    set -a
    source "${PROJECT_DIR}/.env.prod"
    set +a
fi

DB_USER="${POSTGRES_USER:-worldcup}"
DB_NAME="${POSTGRES_DB:-worldcup_predictions}"
CONTAINER="${POSTGRES_CONTAINER:-worldcup-db}"

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting backup..."

docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

echo "[$(date)] Backup saved: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

find "$BACKUP_DIR" -name "*.sql.gz" -mtime +"$KEEP_DAYS" -delete

echo "[$(date)] Cleaned backups older than ${KEEP_DAYS} days"