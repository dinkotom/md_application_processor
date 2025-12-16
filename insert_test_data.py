import sqlite3
import sys

db_path = 'applications_test.db'
print(f"Connecting to {db_path}...")

try:
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()
    
    email = 'invalid-email-format'
    
    # Check if exists
    cursor.execute('SELECT id FROM applicants WHERE email = ?', (email,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"Applicant already exists with ID: {existing[0]}")
    else:
        print("Executing INSERT...")
        cursor.execute('''
            INSERT INTO applicants (first_name, last_name, email, membership_id, status) 
            VALUES ('Test', 'InvalidEmail', ?, '99999', 'Nová')
        ''', (email,))
        
        new_id = cursor.lastrowid
        conn.commit()
        print(f"Successfully inserted applicant with ID: {new_id}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
