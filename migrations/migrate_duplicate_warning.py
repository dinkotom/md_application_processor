#!/usr/bin/env python3
"""
Migration to add duplicate_warning_dismissed column
"""
import sqlite3
import sys

def migrate_database(db_path):
    """Add duplicate_warning_dismissed column"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(applicants)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'duplicate_warning_dismissed' not in columns:
            cursor.execute('ALTER TABLE applicants ADD COLUMN duplicate_warning_dismissed INTEGER DEFAULT 0')
            print(f"✓ Added duplicate_warning_dismissed column to {db_path}")
        else:
            print(f"ℹ Column already exists in {db_path}")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed for {db_path}: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    # Migrate both databases
    databases = ['applications_test.db', 'applications.db']
    
    for db in databases:
        try:
            migrate_database(db)
        except Exception as e:
            print(f"Error migrating {db}: {e}")
            sys.exit(1)
    
    print("\n✓ Migration completed successfully")
