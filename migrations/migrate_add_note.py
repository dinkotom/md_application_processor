#!/usr/bin/env python3
"""
Migration script to add note column to applicants table
"""

import sqlite3
import os

def migrate_add_note_column(db_path):
    """Add note column to applicants table"""
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Skipping migration.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(applicants)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'note' not in columns:
        print(f"Adding 'note' column to {db_path}...")
        cursor.execute('ALTER TABLE applicants ADD COLUMN note TEXT')
        conn.commit()
        print("Migration completed successfully!")
    else:
        print(f"Column 'note' already exists in {db_path}. Skipping.")
    
    conn.close()

if __name__ == '__main__':
    # Migrate both databases
    migrate_add_note_column('applications_test.db')
    migrate_add_note_column('applications.db')
