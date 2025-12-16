import unittest
import sys
import os
import sqlite3

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app, session
from src.database import get_db_path, init_db

class TestClearDBSuccess(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.secret_key = 'test_secret'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        
        self.db_path = get_db_path()
        init_db(self.db_path)
        
        # Login
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}
            sess['mode'] = 'test'
            
        # Clean functionality
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM applicants')
        conn.execute('DELETE FROM audit_logs')
        conn.commit()
        conn.close()

    def tearDown(self):
        self.ctx.pop()

    def test_clear_database_success(self):
        """Test that clear_database runs without error and clears tables"""
        # 1. Insert Data
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO applicants (first_name, deleted) VALUES ('ToDelete', 0)")
        conn.execute("INSERT INTO audit_logs (applicant_id, action, user) VALUES (1, 'CREATE', 'admin')")
        conn.commit()
        
        # Verify data exists
        count = conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
        self.assertEqual(count, 1)
        conn.close()
        
        # 2. Call Clear Database
        response = self.client.post('/clear_database')
        
        # 3. Expect Redirect (Success)
        self.assertEqual(response.status_code, 302)
        
        # 4. Verify DB is Empty
        conn = sqlite3.connect(self.db_path)
        count_final = conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
        conn.close()
        
        self.assertEqual(count_final, 0, "Database was not cleared")

if __name__ == '__main__':
    unittest.main()
