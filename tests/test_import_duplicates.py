import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import sqlite3

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app, session
from src.database import get_db_path, init_db

class TestImportDuplicates(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.secret_key = 'test_secret'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        
        # Ensure we are in TEST mode
        session['mode'] = 'test'
        
        # Reset DB
        self.db_path = get_db_path()
        init_db(self.db_path)
        
        # Ensure clean state
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM applicants')
        conn.commit()
        conn.close()
        
        # Log in
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}
            sess['mode'] = 'test'

    def tearDown(self):
        self.ctx.pop()
        # Clean up DB? Or init_db handles it next time.

    @patch('src.fetcher.get_unread_emails')
    def test_reimport_deleted_applicant(self, mock_get_emails):
        """Test that a deleted applicant is NOT considered a duplicate"""
        
        email = "deleted.user@example.com"
        
        # 1. Insert a "Deleted" applicant
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, deleted, status)
            VALUES (?, ?, ?, 1, 'Nová')
        ''', ('Old', 'User', email))
        conn.commit()
        conn.close()
        
        # 2. Mock incoming email with SAME address
        mock_body = f"""
Jak se jmenuješ?: New
Jaké je tvé příjmení?: User
Kam ti můžeme poslat e-mail?: {email}

9999
        """
        # (uid, body, date)
        # Parser expects 'str' for body
        mock_get_emails.return_value = [('123', mock_body, '01-Jan-2025')]
        
        # 3. Request Preview
        response = self.client.post('/fetch/preview')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        
        # Should contain 1 email
        self.assertEqual(len(data['emails']), 1)
        
        # Check duplicate flag
        # BEFORE FIX: This would satisfy 'is_duplicate' == True
        # AFTER FIX: This must be False
        first_email = data['emails'][0]
        self.assertFalse(first_email['is_duplicate'], "Deleted applicant should NOT be flagged as duplicate")
        self.assertEqual(data['duplicates'], 0)
        self.assertEqual(data['new'], 1)

        # 4. Request Confirm (Import)
        # Session needs 'fetched_emails' which is set by preview, but since we are mocking and using client
        # the session in 'preview' request is saved to cookiejar in client.
        # But `mock_get_emails` is called again in confirm (test mode calls it again with cache logic or simple refetch)
        # Wait, my fix in `fetch_confirm` calls `get_unread_emails` again.
        
        response = self.client.post('/fetch/confirm')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1, "Should import 1 new applicant")
        
        # 5. Verify Database has 2 records (1 deleted, 1 active)
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute('SELECT id, deleted FROM applicants WHERE email = ?', (email,)).fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 2, "Should have 2 records for this email")
        
        deleted_rows = [r for r in rows if r[1] == 1]
        active_rows = [r for r in rows if r[1] == 0]
        
        self.assertEqual(len(deleted_rows), 1, "One should be deleted")
        self.assertEqual(len(active_rows), 1, "One should be active")

if __name__ == '__main__':
    unittest.main()
