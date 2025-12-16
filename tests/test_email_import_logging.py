import unittest
import sqlite3
import os
import sys
from unittest.mock import patch, MagicMock
from flask import session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import create_app
from src.database import get_db_path, init_db, DB_PATH_TEST

class TestEmailImportLogging(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.secret_key = 'test_secret'
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Setup DB
        with self.app.app_context():
            self.db_path = DB_PATH_TEST 
            # We need to manually set DB to test mode or rely on 'test' mode logic
            
            # Reset DB
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            init_db(self.db_path)
            
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
    def _create_applicant(self, email, first_name="Test", last_name="User", deleted=0, membership_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applicants (first_name, last_name, email, deleted, membership_id)
            VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, email, deleted, membership_id))
        
        # Clear logs for clean state if needed
        # conn.execute("DELETE FROM audit_logs")
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def _get_logs(self, applicant_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        logs = conn.execute("SELECT * FROM audit_logs WHERE applicant_id = ? ORDER BY id DESC", (applicant_id,)).fetchall()
        conn.close()
        return logs

    @patch('src.fetcher.get_unread_emails')
    @patch('src.parser.parse_email_body')
    def test_import_new_applicant(self, mock_parser, mock_fetcher):
        """Test that importing a new applicant creates an audit log."""
        
        # Mock Fetcher Return: (uid, body, date)
        mock_fetcher.return_value = [('100', 'Dummy Body', '2025-01-01')]
        
        # Mock Parser Return
        mock_parser.return_value = {
            'first_name': 'New',
            'last_name': 'Import',
            'email': 'new.import@example.com',
            'membership_id': '99999' # Important: Must have membership_id to proceed in fetch_confirm
        }
        
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'test'
            
        resp = self.client.post('/fetch/confirm')
        self.assertEqual(resp.status_code, 200, f"Response: {resp.data}")
        
        # Verify DB
        conn = sqlite3.connect(self.db_path)
        user = conn.execute("SELECT * FROM applicants WHERE email = ?", ('new.import@example.com',)).fetchone()
        conn.close()
        
        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'New') # first_name is 2nd col usually, or verify by dict if row factory set
        
        # Verify Logs
        logs = self._get_logs(user[0]) # ID is first col
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['action'], "Vytvořeno z emailu")
        self.assertEqual(logs[0]['user'], 'admin@test.com')

    @patch('src.fetcher.get_unread_emails')
    @patch('src.parser.parse_email_body')
    def test_import_duplicate_log(self, mock_parser, mock_fetcher):
        """Test that existing active applicant generates a duplicate log."""
        
        # Create existing user
        user_id = self._create_applicant(
            email='dup@example.com', 
            first_name='Dup', 
            last_name='User', 
            membership_id='88888'
        )
        
        # Mock Fetcher
        mock_fetcher.return_value = [('101', 'Dummy Body', '2025-01-01')]
        
        # Mock Parser to return SAME membership_id
        mock_parser.return_value = {
            'first_name': 'Dup',
            'last_name': 'User',
            'email': 'dup@example.com',
            'membership_id': '88888'
        }
        
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'test'
            
        resp = self.client.post('/fetch/confirm')
        self.assertEqual(resp.status_code, 200)
        
        # Verify Logs
        logs = self._get_logs(user_id)
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['action'], "Pokus o import z emailu (duplicita)")

    @patch('src.fetcher.get_unread_emails')
    @patch('src.parser.parse_email_body')
    def test_import_restore_log(self, mock_parser, mock_fetcher):
        """Test that soft-deleted applicant is restored and logged."""
        
        # Create soft-deleted user
        user_id = self._create_applicant(
            email='deleted@example.com', 
            first_name='Del', 
            last_name='User', 
            deleted=1,
            membership_id='77777'
        )
        
        mock_fetcher.return_value = [('102', 'Dummy Body', '2025-01-01')]
        
        mock_parser.return_value = {
            'first_name': 'Del',
            'last_name': 'User',
            'email': 'deleted@example.com',
            'membership_id': '77777'
        }
        
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'test'
            
        resp = self.client.post('/fetch/confirm')
        self.assertEqual(resp.status_code, 200)
        
        # Verify Restored
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM applicants WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        
        self.assertEqual(user['deleted'], 0, "User should be restored (deleted=0)")
        
        # Verify Logs
        logs = self._get_logs(user_id)
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['action'], "Obnoveno z emailu")

if __name__ == '__main__':
    unittest.main()
