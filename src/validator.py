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
            newsletter INTEGER NOT NULL DEFAULT 1,
            full_body TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            application_received TIMESTAMP,
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


def is_suspect_parent_email(first_name: str, last_name: str, email: str) -> bool:
    """
    Checks if email address appears to belong to someone else (e.g., parent).
    Returns True if the email doesn't contain any part of the applicant's name.
    """
    if not (first_name and last_name and email):
        return False
    
    import unicodedata
    
    def normalize(text):
        """Remove diacritics and convert to lowercase"""
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    
    # Get email local part (before @)
    email_local = email.split('@')[0].lower()
    
    # Normalize names
    first = normalize(first_name.strip())
    last = normalize(last_name.strip())
    
    # Check if any significant part of the name appears in email
    # Significant = at least 3 characters
    first_parts = [p for p in first.split() if len(p) >= 3]
    last_parts = [p for p in last.split() if len(p) >= 3]
    
    for part in first_parts + last_parts:
        if part in email_local:
            return False  # Name found in email, looks legitimate
    
    # Also check for initials (first letter of first + last name)
    if len(first) > 0 and len(last) > 0:
        initials = first[0] + last[0]
        if initials in email_local:
            return False
    
    # No match found - suspect parent/other person's email
    return True

def check_duplicate_contact(email: str, phone: str, current_id: int = None, db_path: str = DB_PATH) -> dict:
    """
    Checks if email or phone number is already used by another applicant.
    Returns a dict with 'email_duplicate' and 'phone_duplicate' booleans.
    """
    result = {'email_duplicate': False, 'phone_duplicate': False}
    
    if not (email or phone):
        return result
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check email duplicate
    if email:
        query = 'SELECT id FROM applicants WHERE email = ? AND deleted = 0'
        params = [email.strip()]
        
        if current_id is not None:
            query += ' AND id != ?'
            params.append(current_id)
            
        cursor.execute(query, tuple(params))
        if cursor.fetchone():
            result['email_duplicate'] = True
            
    # Check phone duplicate
    if phone:
        # Simple phone normalization (remove spaces)
        clean_phone = phone.replace(' ', '').replace('-', '')
        if len(clean_phone) > 5: # Only check if phone is substantial
            # This is tricky because phones in DB might be formatted differently
            # For now, let's just check exact match of what's in DB vs input
            # Ideally we would normalize everything in DB or use a LIKE query
            
            query = 'SELECT id FROM applicants WHERE replace(replace(phone, " ", ""), "-", "") = ? AND deleted = 0'
            params = [clean_phone]
            
            if current_id is not None:
                query += ' AND id != ?'
                params.append(current_id)
                
            cursor.execute(query, tuple(params))
            if cursor.fetchone():
                result['phone_duplicate'] = True
    
    conn.close()
    return result


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
    newsletter = data.get('newsletter', 0)  # Now an integer (0 or 1)
    full_body = data.get('full_body', '').strip()
    application_received = data.get('application_received')  # Can be None for CSV imports
    
    try:
        cursor.execute('''
            INSERT INTO applicants (
                first_name, last_name, email, phone, dob, membership_id,
                city, school, interests, character, frequency, source,
                source_detail, message, color, newsletter, full_body, application_received
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fn, ln, em, ph, dob, mid, city, school, interests, character, 
              frequency, source, source_detail, message, color, newsletter, full_body, application_received))
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
