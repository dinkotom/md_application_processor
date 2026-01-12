
import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate(db_path):
    """
    Add 'filter_status' column to export_presets table
    """
    logger.info(f"Checking for 'filter_status' column in export_presets on {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists (should be created by migrate_export_presets)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='export_presets'")
        if not cursor.fetchone():
             logger.warning("Table 'export_presets' does not exist yet. Skipping column add (migrate_export_presets should run first).")
             conn.close()
             return

        cursor.execute("PRAGMA table_info(export_presets)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'filter_status' not in columns:
            logger.info("Adding 'filter_status' column...")
            cursor.execute("ALTER TABLE export_presets ADD COLUMN filter_status TEXT")
            conn.commit()
            logger.info("Column added successfully.")
        else:
            logger.info("Column 'filter_status' already exists.")
            
    except Exception as e:
        logger.error(f"Error during migration export_presets_status: {e}")
        conn.rollback()
    finally:
        conn.close()
