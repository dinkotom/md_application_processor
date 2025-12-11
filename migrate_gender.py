
import sqlite3
import os
from src.gender_utils import guess_gender

def migrate_db(db_path):
    print(f"Migrating database: {db_path}")
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Add column if not exists
    try:
        cursor.execute("ALTER TABLE applicants ADD COLUMN guessed_gender TEXT")
        print("Column 'guessed_gender' added.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
             print("Column 'guessed_gender' already exists.")
        else:
            print(f"Error adding column: {e}")
            return

    # 2. Update existing records
    cursor.execute("SELECT id, first_name, last_name FROM applicants")
    rows = cursor.fetchall()
    
    print(f"Updating {len(rows)} records...")
    
    BATCH_SIZE = 100
    updates = []
    
    for row in rows:
        gender = guess_gender(row['first_name'], row['last_name'])
        updates.append((gender, row['id']))
        
        if len(updates) >= BATCH_SIZE:
             cursor.executemany("UPDATE applicants SET guessed_gender = ? WHERE id = ?", updates)
             conn.commit()
             updates = []
             
    if updates:
        cursor.executemany("UPDATE applicants SET guessed_gender = ? WHERE id = ?", updates)
        conn.commit()

    print("Migration complete.")
    conn.close()

if __name__ == "__main__":
    # Migrate both test and prod
    migrate_db("applications_test.db")
    migrate_db("applications.db")
