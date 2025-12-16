import sqlite3
import os

DB_PATH = 'applications_test.db'

def setup_test_data():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Initialize DB (using the schema from validator.py effectively)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applicants (
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
            newsletter TEXT,
            full_body TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Nová',
            exported_to_ecomail INTEGER DEFAULT 0,
            exported_at TIMESTAMP
        )
    ''')
    
    # Insert Applicant 1
    cursor.execute('''
        INSERT INTO applicants (first_name, last_name, email, membership_id, dob, city)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Jan', 'Novák', 'jan.novak@example.com', '1001', '01.01.2000', 'Praha'))
    
    # Insert Applicant 2 (Duplicate Name/Email, different ID)
    cursor.execute('''
        INSERT INTO applicants (first_name, last_name, email, membership_id, dob, city)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Jan', 'Novák', 'jan.novak@example.com', '1002', '01.01.2000', 'Brno'))
    
    conn.commit()
    conn.close()
    print("Test data with duplicates created.")

if __name__ == "__main__":
    setup_test_data()
