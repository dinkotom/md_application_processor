import sqlite3
import os

DB_PATHS = ["applications.db", "applications_test.db"]

def migrate_db(db_path):
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist, skipping.")
        return

    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(applicants)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "application_received" not in columns:
            print(f"Adding 'application_received' column to {db_path}...")
            cursor.execute("ALTER TABLE applicants ADD COLUMN application_received TIMESTAMP")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'application_received' column already exists.")
            
    except Exception as e:
        print(f"Error migrating {db_path}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    for db in DB_PATHS:
        migrate_db(db)
