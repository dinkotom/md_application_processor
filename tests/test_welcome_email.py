import unittest
import sqlite3
import os
import sys
from io import BytesIO
from unittest.mock import patch, MagicMock, ANY
from flask import session

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import create_app
from src.database import get_db_path, init_db, DB_PATH_TEST

class TestWelcomeEmail(unittest.TestCase):
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
            
            # Setup Environment Mocks for Email
            self.email_user = 'mock_sender@example.com'
            self.email_pass = 'mock_pass'
            # We will patch os.getenv in the test method or use patcher in setUp
            
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
    def test_send_welcome_email_flow(self, mock_get_db_path, mock_getenv, mock_gen_card, mock_load_template, mock_smtp):
        """test sending welcome email: headers, content, db update, audit log"""
        
        # Force DB Path to Test DB even if mode is production
        mock_get_db_path.return_value = self.db_path
        
        # 1. Setup Data
        applicant_id = self._create_applicant()
        
        # 2. Configure Mocks
        # Environment variables
        def getenv_side_effect(key, default=None):
            if key == 'EMAIL_USER': return self.email_user
            if key == 'EMAIL_PASS': return self.email_pass
            if key == 'IMAP_SERVER': return 'imap.mock.com'
            if key == 'SMTP_HOST': return 'smtp.custom.com'
            if key == 'SMTP_PORT': return '465'
            return default
        mock_getenv.side_effect = getenv_side_effect
        
        # Card Generator
        # MIMEImage needs a valid header to guess subtype if not provided. Use minimal PNG signature.
        mock_gen_card.return_value = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
        
        # Template Loader
        mock_load_template.return_value = ("<html><body>Hello {first_name}!</body></html>", "/path/to/template")
        
        # SMTP Server Mock
        mock_server_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server_instance
        
        # 3. Request
        # We need to be logged in
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'test' 
            # In test mode, recipient is usually overridden (see src/email_sender.py:get_recipient_email)
            # The user request specifically mentioned "check from: to: subject:".
            # If mode is test, 'To' will be the test email.
            # I should intentionally set mode='production' to verify the Real 'To' address if feasible,
            # or verify the 'test' behavior if that's what's running.
            # Let's test 'production' mode logic for address verification to be precise about target.
            sess['mode'] = 'production'

        resp = self.client.post(f'/applicant/{applicant_id}/send_welcome_email')
        
        # 4. Verifications
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['success'], True)
        
        # A) Verify SMTP calls (Headers & Content)
        mock_server_instance.login.assert_called_with(self.email_user, self.email_pass)
        mock_server_instance.send_message.assert_called_once()
        
        # Inspect the message object passed to send_message
        call_args = mock_server_instance.send_message.call_args
        msg = call_args[0][0] # First arg is the message
        
        # Verify SMTP init with custom host/port
        mock_smtp.assert_called_with('smtp.custom.com', 465)
        # Verify From Header
        self.assertEqual(msg['From'], "Mladý divák <info@mladydivak.cz>")
        self.assertEqual(msg['To'], 'jan.novak@example.com') # Because we set mode=production
        self.assertEqual(msg['Subject'], 'Vítej v klubu Mladého diváka')
        self.assertEqual(msg['Reply-To'], 'info@mladydivak.cz')
        
    @patch('src.email_sender.smtplib.SMTP_SSL')
    @patch('src.email_sender.load_welcome_email_template')
    @patch('src.generator.generate_card')
    @patch('os.getenv')
    @patch('src.database.get_db_path')
    def test_mode_recipient_override(self, mock_get_db_path, mock_getenv, mock_gen_card, mock_load_template, mock_smtp):
        """Test that in test mode, email is sent to safe address"""
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
        self.assertEqual(resp.json['success'], True)
        self.assertEqual(resp.json['mode'], 'test')
        self.assertEqual(resp.json['recipient'], 'u7745030724@gmail.com, admin@test.com')
        
        call_args = mock_server_instance.send_message.call_args
        msg = call_args[0][0]
        
        # MUST be the safe address + copy
        self.assertEqual(msg['To'], 'u7745030724@gmail.com, admin@test.com')
        # MUST NOT be the real user
        self.assertNotEqual(msg['To'], 'jan.novak@example.com')
        
        # Verify Body Content (multipart traversal)
        # The message is multipart/mixed -> multipart/alternative -> text/html
        # or simplified depending on structure.
        # Let's stringify and check existence.
        
        parts = [part for part in msg.walk() if part.get_content_type() == 'text/html']
        self.assertTrue(len(parts) > 0, "No HTML part found in email")
        html_payload = parts[0].get_payload(decode=True).decode('utf-8')
        
        # Only simple replacements happen in current logic for {first_name} etc if render_email_template is called.
        # Wait, src/email_sender.py line 52 says: "# Template no longer uses dynamic content replacement for name" in render_html_email_template
        # But line 124 calls render_email_template if !use_html.
        # Line 210 calls with use_html=True.
        # So render_html_email_template is called. It passes result = template_html and does 'pass'.
        # So it seems dynamic replacement for HTML body is DISABLED in current code?
        # Let's check src/email_sender.py again.
        # Yes: def render_html_email_template(template_html, applicant_data): ... pass ... return result
        # So checking for "Hello Jan!" might fail if the code doesn't actually replace it.
        # I will check that the raw template was used.
        self.assertIn("Test", html_payload)
        
        # B) Verify DB Update (email_sent)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM applicants WHERE id = ?", (applicant_id,)).fetchone()
        self.assertEqual(user['email_sent'], 1)
        self.assertTrue(user['email_sent_at']) # Should be not null/empty
        
        # C) Verify Audit Log
        logs = conn.execute("SELECT * FROM audit_logs WHERE applicant_id = ?", (applicant_id,)).fetchall()
        conn.close()
        
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['action'], "Odeslán uvítací email")
        self.assertEqual(logs[0]['user'], 'admin@test.com')

    @patch('src.email_sender.smtplib.SMTP')
    @patch('src.email_sender.load_welcome_email_template')
    @patch('src.generator.generate_card')
    @patch('os.getenv')
    @patch('src.database.get_db_path')
    def test_send_welcome_email_starttls(self, mock_get_db_path, mock_getenv, mock_gen_card, mock_load_template, mock_smtp):
        """test sending with STARTTLS (port 587)"""
        mock_get_db_path.return_value = self.db_path
        applicant_id = self._create_applicant()

        # Mock env for STARTTLS
        def getenv_side_effect(key, default=None):
            if key == 'EMAIL_USER': return self.email_user
            if key == 'EMAIL_PASS': return self.email_pass
            if key == 'SMTP_HOST': return 'smtp.starttls.com'
            if key == 'SMTP_PORT': return '587'
            return default
        mock_getenv.side_effect = getenv_side_effect
        
        mock_gen_card.return_value = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
        mock_load_template.return_value = ("<html></html>", "path")
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Login
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'production'

        resp = self.client.post(f'/applicant/{applicant_id}/send_welcome_email')



        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['success'], True)

        # Verify SMTP (not SSL) was used
        mock_smtp.assert_called_with('smtp.starttls.com', 587)
        # Verify starttls called
        mock_server.starttls.assert_called_once()
        # Verify login and send
        mock_server.login.assert_called_with(self.email_user, self.email_pass)
        mock_server.send_message.assert_called_once()

if __name__ == '__main__':
    unittest.main()
