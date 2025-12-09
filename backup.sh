#!/bin/bash

# Configuration
# Adjust these paths if running from a different directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_FILE="$PROJECT_DIR/applications.db"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="$BACKUP_DIR/applications_$TIMESTAMP.db"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Perform backup
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_FILE"
    echo "Backup created: $BACKUP_FILE"
    
    # Cleanup: Keep only last 30 backups to save space
    # ls -t "$BACKUP_DIR"/*.db | tail -n +31 | xargs -I {} rm {} 2>/dev/null
else
    echo "Error: Database file $DB_FILE not found!"
    exit 1
fi
