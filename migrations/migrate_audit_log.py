import sqlite3
import os

def migrate_audit_log(db_path):
    """
    Creates the audit_logs table if it doesn't exist.
    """
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Skipping.")
        return

    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                user TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                old_value TEXT,
                new_value TEXT,
                FOREIGN KEY (applicant_id) REFERENCES applicants (id)
            )
        ''')
        conn.commit()
        print(f"Audit log table created successfully in {db_path}")
    except Exception as e:
        print(f"Error creating audit log table in {db_path}: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    migrate_audit_log(os.path.join(base_dir, 'applications_test.db'))
    migrate_audit_log(os.path.join(base_dir, 'applications.db'))
