#!/usr/bin/env python3
"""
Database migration to add email functionality
"""
import sqlite3
import sys

def migrate_database(db_path):
    """Add email template and tracking fields"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create email_template table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add email tracking columns to applicants table
        # Check if columns exist first
        cursor.execute("PRAGMA table_info(applicants)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'email_sent' not in columns:
            cursor.execute('ALTER TABLE applicants ADD COLUMN email_sent INTEGER DEFAULT 0')
        
        if 'email_sent_at' not in columns:
            cursor.execute('ALTER TABLE applicants ADD COLUMN email_sent_at TIMESTAMP')
        
        # Insert default email template if none exists
        cursor.execute('SELECT COUNT(*) FROM email_template')
        if cursor.fetchone()[0] == 0:
            default_subject = "Členská karta Mladý divák"
            default_body = """Dobrý den {first_name} {last_name},

děkujeme za Vaši přihlášku do programu Mladý divák.

V příloze naleznete Vaši členskou kartu (číslo {membership_id}).

S pozdravem,
Tým Mladý divák"""
            
            cursor.execute('''
                INSERT INTO email_template (subject, body)
                VALUES (?, ?)
            ''', (default_subject, default_body))
        
        conn.commit()
        print(f"✓ Migration successful for {db_path}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed for {db_path}: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    # Migrate both databases
    databases = ['applications_test.db', 'applications.db']
    
    for db in databases:
        try:
            migrate_database(db)
        except Exception as e:
            print(f"Error migrating {db}: {e}")
            sys.exit(1)
    
    print("\n✓ All migrations completed successfully")
