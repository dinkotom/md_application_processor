#!/usr/bin/env python3
"""
Migration script to convert newsletter column to INTEGER with NOT NULL constraint and default value.
This migration updates both test and production databases.
"""

import sqlite3
import os

def migrate_newsletter_to_integer(db_path):
    """
    Migrates the newsletter column from TEXT to INTEGER with NOT NULL and default value 1.
    
    SQLite doesn't support ALTER COLUMN directly, so we need to:
    1. Create a new table with the correct schema
    2. Copy data from old table (converting TEXT to INTEGER)
    3. Drop old table
    4. Rename new table
    """
    print(f"Migrating {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Skipping.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if newsletter column exists and its current type
        cursor.execute("PRAGMA table_info(applicants)")
        columns = cursor.fetchall()
        newsletter_col = [col for col in columns if col[1] == 'newsletter']
        
        if not newsletter_col:
            print(f"Newsletter column does not exist in {db_path}. Skipping.")
            conn.close()
            return
        
        # Check if newsletter is already INTEGER
        current_type = newsletter_col[0][2]  # Column type
        if current_type == 'INTEGER':
            print(f"Newsletter column is already INTEGER in {db_path}. Skipping.")
            conn.close()
            return
        
        # Drop temp table if it exists from previous failed migration
        cursor.execute("DROP TABLE IF EXISTS applicants_new")
        
        print("Creating new table with INTEGER newsletter column...")
        
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE applicants_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                dob TEXT,
                membership_id TEXT,
                city TEXT,
                school TEXT,
                interests TEXT,
                character TEXT,
                frequency TEXT,
                source TEXT,
                source_detail TEXT,
                message TEXT,
                color TEXT,
                newsletter INTEGER NOT NULL DEFAULT 1,
                full_body TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Nová',
                exported_to_ecomail INTEGER DEFAULT 0,
                exported_at TIMESTAMP,
                application_received TIMESTAMP,
                email_sent INTEGER DEFAULT 0,
                email_sent_at TIMESTAMP,
                parent_email_warning_dismissed INTEGER DEFAULT 0,
                duplicate_warning_dismissed INTEGER DEFAULT 0,
                note TEXT
            )
        ''')
        
        print("Copying data and converting newsletter values...")
        
        # Get list of existing columns
        cursor.execute("PRAGMA table_info(applicants)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Build column list for INSERT, excluding newsletter which we'll handle specially
        columns_to_copy = [col for col in existing_columns if col != 'newsletter']
        columns_str = ', '.join(columns_to_copy)
        
        # Build SELECT with newsletter conversion
        select_columns = []
        for col in existing_columns:
            if col == 'newsletter':
                # Convert newsletter to INTEGER
                # Handle various formats: 'yes', 'no', empty, NULL, 0, 1, text
                select_columns.append('''
                    CASE 
                        WHEN newsletter IS NULL OR newsletter = '' OR LOWER(newsletter) = 'yes' THEN 1
                        WHEN newsletter = '0' OR newsletter = 0 OR LOWER(newsletter) = 'no' THEN 0
                        WHEN newsletter = '1' OR newsletter = 1 THEN 1
                        ELSE 0
                    END as newsletter
                ''')
            else:
                select_columns.append(col)
        
        select_str = ', '.join(select_columns)
        
        # Build INSERT column list in same order as SELECT
        insert_columns = existing_columns  # Use same order as existing table
        insert_str = ', '.join(insert_columns)
        
        # Copy data with conversion
        cursor.execute(f'''\
            INSERT INTO applicants_new ({insert_str})
            SELECT {select_str}
            FROM applicants
        ''')
        
        # Get count of migrated records
        cursor.execute("SELECT COUNT(*) FROM applicants_new")
        count = cursor.fetchone()[0]
        print(f"Migrated {count} records")
        
        # Drop old table
        cursor.execute("DROP TABLE applicants")
        
        # Rename new table
        cursor.execute("ALTER TABLE applicants_new RENAME TO applicants")
        
        conn.commit()
        print(f"✓ Successfully migrated {db_path}")
        
    except Exception as e:
        print(f"✗ Error migrating {db_path}: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Migrate both databases
    databases = [
        "applications_test.db",
        "applications.db"
    ]
    
    for db in databases:
        migrate_newsletter_to_integer(db)
    
    print("\n✓ Migration complete!")
