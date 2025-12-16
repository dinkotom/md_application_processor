import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add root directory to path to allow importing src and app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app, session
from src.database import get_db_path, DB_PATH_TEST, DB_PATH_PROD
from src.email_sender import get_recipient_email

class TestModeBehaviors(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.secret_key = 'test_secret'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    # --- 1. Database Storage ---
    def test_database_path_selection(self):
        """Test that get_db_path returns correct path based on session mode"""
        
        # Test Mode (Default or explicitly set)
        session['mode'] = 'test'
        self.assertEqual(get_db_path(), DB_PATH_TEST, "Should use TEST db in test mode")

        # Production Mode
        session['mode'] = 'production'
        self.assertEqual(get_db_path(), DB_PATH_PROD, "Should use PROD db in production mode")
        
        # Default (None) -> Test
        if 'mode' in session: del session['mode']
        self.assertEqual(get_db_path(), DB_PATH_TEST, "Should default to TEST db if mode not set")

    # --- 2. Sending Emails ---
    def test_email_recipient_logic(self):
        """Test that get_recipient_email redirects in test mode"""
        real_email = "applicant@example.com"
        
        # Test Mode -> Redirect
        recipient = get_recipient_email(real_email, mode='test')
        self.assertEqual(recipient, 'u7745030724@gmail.com', "Should redirect to test email in test mode")
        
        # Production Mode -> Real Email
        recipient = get_recipient_email(real_email, mode='production')
        self.assertEqual(recipient, real_email, "Should use real email in production mode")

    # --- 3. Importing Emails (Fetch) ---
    @patch('src.fetcher.get_unread_emails')
    def test_import_mark_as_read_logic(self, mock_get_emails):
        """Test that mark_as_read flag is correctly set based on mode"""
        
        # Mock connection and other calls to avoid side effects
        mock_get_emails.return_value = [] # Return empty list to stop execution early
        
        # Authenticate
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}

        # Case A: Test Mode
        with self.client.session_transaction() as sess:
            sess['mode'] = 'test'
        
        # Call fetch confirm
        self.client.post('/fetch/confirm')
        
        # Verify call args
        # call_args is (args, kwargs)
        # We expect mark_as_read=False
        _, kwargs = mock_get_emails.call_args
        self.assertFalse(kwargs.get('mark_as_read'), "In TEST mode, mark_as_read should be False")

        # Case B: Production Mode
        with self.client.session_transaction() as sess:
            sess['mode'] = 'production'
            
        self.client.post('/fetch/confirm')
        
        # Verify call args
        _, kwargs = mock_get_emails.call_args
        self.assertTrue(kwargs.get('mark_as_read'), "In PROD mode, mark_as_read should be True")

    # --- 4. Database Management ---
    @patch('routes.settings.get_db_connection')
    def test_clear_database_protection(self, mock_conn):
        """Test that clearing database is forbidden in production"""
        
        # Authenticate
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}

        # Case A: Test Mode -> Should Allow (Redirects to advanced)
        with self.client.session_transaction() as sess:
            sess['mode'] = 'test'
            
        response = self.client.post('/clear_database')
        
        # Verify it TRIED to clear (mock called)
        self.assertTrue(mock_conn.called, "Should attempt to connect to DB in test mode")
        
        self.assertNotEqual(response.status_code, 403, "Should allow clearing DB in test mode")
        
        # Case B: Production Mode -> Should Forbid (403)
        with self.client.session_transaction() as sess:
            sess['mode'] = 'production'
            
        response = self.client.post('/clear_database')
        self.assertEqual(response.status_code, 403, "Should forbid clearing DB in production mode")

if __name__ == '__main__':
    unittest.main()
