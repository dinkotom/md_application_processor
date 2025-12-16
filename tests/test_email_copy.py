import unittest
import sqlite3
import os
import sys
from io import BytesIO
from unittest.mock import patch, MagicMock
from flask import session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import create_app
from src.database import init_db, DB_PATH_TEST

class TestEmailCopy(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.secret_key = 'test_secret'
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Setup DB
        with self.app.app_context():
            self.db_path = DB_PATH_TEST
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            init_db(self.db_path)
            
            self.email_user = 'mock_sender@example.com'
            self.email_pass = 'mock_pass'
            
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_applicant(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applicants (first_name, last_name, email, membership_id)
            VALUES (?, ?, ?, ?)
        """, ('Jan', 'Novak', 'jan.novak@example.com', '12345'))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    @patch('src.email_sender.smtplib.SMTP_SSL')
    @patch('src.email_sender.load_welcome_email_template')
    @patch('src.generator.generate_card')
    @patch('os.getenv')
    @patch('src.database.get_db_path')
    def test_copy_to_logged_in_user_in_test_mode(self, mock_get_db_path, mock_getenv, mock_gen_card, mock_load_template, mock_smtp):
        """Test that in test mode, the logged-in user is added to recipients"""
        mock_get_db_path.return_value = self.db_path
        
        # 1. Setup Data
        applicant_id = self._create_applicant()
        
        # 2. Configure Mocks
        def getenv_side_effect(key, default=None):
            if key == 'EMAIL_USER': return self.email_user
            if key == 'EMAIL_PASS': return self.email_pass
            if key == 'IMAP_SERVER': return 'imap.mock.com'
            return default
        mock_getenv.side_effect = getenv_side_effect
        
        mock_gen_card.return_value = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
        mock_load_template.return_value = ("<html>Test</html>", "/path")
        
        mock_server_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server_instance
        
        # 3. Request in TEST mode
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'test' 
            
        resp = self.client.post(f'/applicant/{applicant_id}/send_welcome_email')
        
        # 4. Verify
        self.assertEqual(resp.status_code, 200)
        
        # Verify To Header
        call_args = mock_server_instance.send_message.call_args
        msg = call_args[0][0]
        to_header = msg['To']
        
        print(f"DEBUG: To Header = {to_header}")
        
        # Should contain both
        self.assertIn('u7745030724@gmail.com', to_header)
        self.assertIn('admin@test.com', to_header)
        
        # Just to be sure, in production mode it should NOT verify this
        # (Optional, but good verification)
