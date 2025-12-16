import sqlite3
import os

def migrate(db_path):
    print(f"Running migration: create export_presets table on {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS export_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                fields TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Table export_presets created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Default to test DB if run directly
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'applications_test.db')
    migrate(db_path)
