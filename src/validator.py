import sqlite3
import os
import os

DB_PATH = "applications.db"

def init_db(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
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
    conn.commit()
    conn.close()

def is_duplicate(membership_id: str, db_path: str = DB_PATH) -> bool:
    """Checks if the applicant already exists in the database by membership_id."""
    if not membership_id:
        return False
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    mid = str(membership_id).strip()
    
    cursor.execute('SELECT id FROM applicants WHERE membership_id = ?', (mid,))
    
    result = cursor.fetchone()
    conn.close()
    return result is not None

def is_suspect_duplicate(first_name: str, last_name: str, email: str, db_path: str = DB_PATH) -> bool:
    """Checks if a potential duplicate applicant exists based on first name, last name, and email."""
    if not (first_name and last_name and email):
        return False # Not enough info to check for suspect duplicate

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check for existing records with the same first name, last name, and email
    cursor.execute('''
        SELECT id FROM applicants
        WHERE first_name = ? AND last_name = ? AND email = ?
    ''', (first_name.strip(), last_name.strip(), email.strip()))

    result = cursor.fetchone()
    conn.close()
    return result is not None

def record_applicant(data: dict, db_path: str = DB_PATH):
    """Records the applicant in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    fn = data.get('first_name', '').strip()
    ln = data.get('last_name', '').strip()
    em = data.get('email', '').strip()
    ph = data.get('phone', '').strip()
    dob = data.get('dob', '').strip()
    mid = data.get('membership_id', '').strip()
    city = data.get('city', '').strip()
    school = data.get('school', '').strip()
    interests = data.get('interests', '').strip()
    character = data.get('character', '').strip()
    frequency = data.get('frequency', '').strip()
    source = data.get('source', '').strip()
    source_detail = data.get('source_detail', '').strip()
    message = data.get('message', '').strip()
    color = data.get('color', '').strip()
    newsletter = data.get('newsletter', '').strip()
    full_body = data.get('full_body', '').strip()
    
    try:
        cursor.execute('''
            INSERT INTO applicants (
                first_name, last_name, email, phone, dob, membership_id,
                city, school, interests, character, frequency, source,
                source_detail, message, color, newsletter, full_body
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fn, ln, em, ph, dob, mid, city, school, interests, character, 
              frequency, source, source_detail, message, color, newsletter, full_body))
        conn.commit()
    except sqlite3.IntegrityError:
        # Already exists, ignore
        pass
    finally:
        conn.close()

def clear_db(db_path: str = DB_PATH):
    """Clears the database (for testing)."""
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
