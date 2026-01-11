import sqlite3
import os
import logging
from flask import session

import unicodedata

logger = logging.getLogger(__name__)

def remove_diacritics(text):
    """
    Remove diacritics from text (comparable to unaccent in PostgreSQL).
    Example: 'Štěpánka' -> 'stepanka', 'Malečková' -> 'maleckova'
    """
    if not text:
        return ""
    text = str(text)
    # Normalize unicode to decompose characters
    nfkd_form = unicodedata.normalize('NFKD', text)
    # Filter out non-spacing mark characters
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

# Database paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH_TEST = os.path.join(BASE_DIR, 'applications_test.db')
DB_PATH_PROD = os.path.join(BASE_DIR, 'applications.db')

def get_db_path():
    """Get database path based on current mode"""
    mode = session.get('mode', 'test')
    return DB_PATH_PROD if mode == 'production' else DB_PATH_TEST

def get_db_connection():
    """Get database connection"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.create_function("remove_diacritics", 1, remove_diacritics)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    """Initialize database with schema if it doesn't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create applicants table
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
            status TEXT DEFAULT 'Nová',
            deleted INTEGER DEFAULT 0,
            exported_to_ecomail INTEGER DEFAULT 0,
            exported_at TIMESTAMP,
            application_received TIMESTAMP,
            email_sent INTEGER DEFAULT 0,
            email_sent_at TIMESTAMP,
            parent_email_warning_dismissed INTEGER DEFAULT 0,
            duplicate_warning_dismissed INTEGER DEFAULT 0,
            note TEXT,
            guessed_gender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(first_name, last_name, email)
        );
    ''')
    
    # Create audit_logs table
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
        );
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized: {db_path}")

def log_action(applicant_id, action, user_email, old_value=None, new_value=None, db_path=None, connection=None):
    """
    Log an action to the audit_logs table
    """
    should_close = False
    
    try:
        if connection:
            conn = connection
        else:
            if db_path is None:
                db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            should_close = True
            
        cursor = conn.cursor()
        
        # Serialize values if they are complex objects
        import json
        if isinstance(old_value, (dict, list)):
            old_value = json.dumps(old_value, ensure_ascii=False)
        if isinstance(new_value, (dict, list)):
            new_value = json.dumps(new_value, ensure_ascii=False)
            
        cursor.execute('''
            INSERT INTO audit_logs (applicant_id, action, user, old_value, new_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (applicant_id, action, user_email, old_value, new_value))
        
        if should_close:
            conn.commit()
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to log action: {e}")
        try:
            import datetime
            with open("/tmp/import_debug.log", "a") as f:
                f.write(f"{datetime.datetime.now()} - LOGGING FAILED in database.py: {e}\n")
        except:
            pass
