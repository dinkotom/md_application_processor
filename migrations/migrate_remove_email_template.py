#!/usr/bin/env python3
"""
Database migration to remove email_template table
"""
import sqlite3
import sys

def migrate_database(db_path):
    """Remove email_template table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop email_template table
        cursor.execute('DROP TABLE IF EXISTS email_template')
        
        conn.commit()
        print(f"✓ Migration successful for {db_path}")
        print(f"  - Dropped email_template table")
        
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
    
    print("\n✓ All migrations completed successfully")
