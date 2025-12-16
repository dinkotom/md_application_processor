import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_database(db_path):
    """
    Add 'phone_warning_dismissed' column to applicants table
    """
    logger.info(f"Checking for 'phone_warning_dismissed' column in {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(applicants)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'phone_warning_dismissed' not in columns:
            logger.info("Adding 'phone_warning_dismissed' column...")
            cursor.execute("ALTER TABLE applicants ADD COLUMN phone_warning_dismissed INTEGER DEFAULT 0")
            conn.commit()
            logger.info("Column added successfully.")
        else:
            logger.info("Column 'phone_warning_dismissed' already exists.")
            
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()
