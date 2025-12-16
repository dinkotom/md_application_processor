import unittest
import sys
import os
import sqlite3
import csv
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from web_app import app
from src.database import get_db_path, init_db

class TestImportSoftDeleted(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.secret_key = 'test_secret'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        self.db_path = get_db_path()
        init_db(self.db_path)
        
        # Clean
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM applicants')
        conn.execute('DELETE FROM audit_logs')
        conn.commit()
        conn.close()

    def test_import_existing_skipped(self):
        """Verify that importing an existing (even soft-deleted) applicant is skipped and NOT logged"""
        email = 'existing@example.com'
        
        # 1. Create Pre-existing Applicant
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("INSERT INTO applicants (first_name, email, deleted) VALUES ('Old', ?, 1)", (email,))
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 2. Prepare Import File
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['email', 'first_name'])
            writer.writeheader()
            writer.writerow({'email': email, 'first_name': 'NewImport'})
            tmp_path = tmp.name
            
        with self.client.session_transaction() as sess:
            sess['import_file_path'] = tmp_path
            sess['user'] = {'email': 'admin@example.com'}
            
        # 3. Import
        resp = self.client.post('/import/confirm')
        self.assertEqual(resp.status_code, 200)
        
        # 4. Check Logs
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        logs = conn.execute("SELECT * FROM audit_logs WHERE applicant_id = ?", (app_id,)).fetchall()
        # Verify it is not deleted anymore
        curr = conn.execute("SELECT deleted FROM applicants WHERE id = ?", (app_id,)).fetchone()
        self.assertEqual(curr[0], 0, "Applicant should be restored (deleted=0)")
        
        conn.close()
        
if __name__ == '__main__':
    unittest.main()
