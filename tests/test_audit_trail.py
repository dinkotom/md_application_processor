import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import sqlite3
import json

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app
from src.database import get_db_path, init_db, log_action

class TestAuditTrail(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.secret_key = 'test_secret'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        
        self.db_path = get_db_path()
        init_db(self.db_path)
        
        # Clean state
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM applicants')
        conn.execute('DELETE FROM audit_logs')
        conn.commit()
        conn.close()
        
        # Login
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}

    def tearDown(self):
        self.ctx.pop()
        
    def _get_logs(self, applicant_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Order by ID desc to ensure correct order even if timestamps are same second
        logs = conn.execute('SELECT * FROM audit_logs WHERE applicant_id = ? ORDER BY id DESC', (applicant_id,)).fetchall()
        conn.close()
        return logs

    @patch('src.ecomail.requests')
    def test_log_actions(self, mock_requests):
        """Test audit logging for various actions"""
        
        # 1. Test Creation (via direct DB for now, as import is complex to mock fully in 1 step without file)
        # However, checking the CODE showed no log_action in import_confirm. 
        # Let's try to verify what HAPPENS when we fix it. 
        # For now, let's verify UPDATE works.
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO applicants (first_name, email, status) VALUES ('Test', 't@t.com', 'Nová')")
        app_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 2. Update Status
        resp = self.client.post(f'/applicant/{app_id}/status', data={'status': 'Přijat'})
        self.assertEqual(resp.status_code, 302) # Redirects
        
        logs = self._get_logs(app_id)
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['action'], 'Změna stavu')
        self.assertEqual(logs[0]['new_value'], 'Přijat')

        # 3. Update Field
        resp = self.client.post(f'/applicant/{app_id}/update_field', 
                               json={'field': 'note', 'value': 'New Note'})
        self.assertEqual(resp.status_code, 200)
        
        logs = self._get_logs(app_id)
        # Should be latest
        self.assertEqual(logs[0]['action'], 'Uprava pole note') 
        self.assertEqual(logs[0]['new_value'], 'New Note')
        
        # 4. Delete
        resp = self.client.post(f'/applicant/{app_id}/delete')
        self.assertEqual(resp.status_code, 302)
        
        
        logs = self._get_logs(app_id)
        self.assertEqual(logs[0]['action'], 'Smazání přihlášky')

        # 5. Export to Ecomail
        # Restore applicant first (deleted applicants might be skipped by export logic or selector)
        conn = sqlite3.connect(self.db_path)
        conn.execute('UPDATE applicants SET deleted = 0 WHERE id = ?', (app_id,))
        conn.commit()
        conn.close()
        
        # Mock requests for export
        mock_requests.get.return_value.status_code = 404 # Not found -> Create
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {'success': True}

        resp = self.client.post(f'/applicant/{app_id}/export_to_ecomail')
        self.assertEqual(resp.status_code, 200)
        
        logs = self._get_logs(app_id)
        self.assertEqual(logs[0]['action'], 'Export do Ecomailu')

    def test_import_logging(self):
        """Verify that import creates a log entry"""
        # Create a temp file
        import tempfile
        import csv
        
        # Determine path (mock session uses /tmp/...)
        email = 'import_test@example.com'
        
        # We need to simulate the state where file is already in session['import_file_path']
        # and confirm is called.
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['email', 'first_name'])
            writer.writeheader()
            writer.writerow({'email': email, 'first_name': 'Importer'})
            tmp_path = tmp.name
            
        with self.client.session_transaction() as sess:
            sess['import_file_path'] = tmp_path
            
        # Call confirm
        resp = self.client.post('/import/confirm')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()['success'])
        
        # Verify applicant is created
        conn = sqlite3.connect(self.db_path)
        app = conn.execute("SELECT id FROM applicants WHERE email = ?", (email,)).fetchone()
        app_id = app[0]
        conn.close()
        
        logs = self._get_logs(app_id)
        
        self.assertTrue(len(logs) > 0, "Import should generate an audit log")
        self.assertIn(logs[0]['action'], ['Vytvořeno importem', 'Import'], "Should confirm import action")
        
    def test_import_logging_no_user_email(self):
        """Verify import logging when user email is missing from session"""
        import tempfile
        import csv
        
        email = 'import_no_email@example.com'
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['email', 'first_name'])
            writer.writeheader()
            writer.writerow({'email': email, 'first_name': 'Anonymous'})
            tmp_path = tmp.name
            
        with self.client.session_transaction() as sess:
            sess['import_file_path'] = tmp_path
            # Set user to dict without email to simulate weird auth state but still logged in
            sess['user'] = {'name': 'No Email User'}
                
        # Call confirm
        resp = self.client.post('/import/confirm')
        self.assertEqual(resp.status_code, 200)
        
        conn = sqlite3.connect(self.db_path)
        app = conn.execute("SELECT id FROM applicants WHERE email = ?", (email,)).fetchone()
        app_id = app[0]
        conn.close()
        
        logs = self._get_logs(app_id)
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['user'], 'unknown_import')

    @patch('src.email_sender.send_welcome_email')
    @patch('src.generator.generate_card')
    def test_welcome_email_logging(self, mock_generate_card, mock_send_email):
        """Test audit logging for welcome email"""
        # Create applicant
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO applicants (first_name, email, membership_id) VALUES ('Test', 't@t.com', '1000')")
        app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        # Mock successful card generation
        mock_generate_card.return_value = b'fake_image_data'
        
        # Mock successful email sending
        mock_send_email.return_value = {'success': True}

        # Mock Env variables
        with patch.dict(os.environ, {'EMAIL_USER': 'me@test.com', 'EMAIL_PASS': 'secret'}):
            resp = self.client.post(f'/applicant/{app_id}/send_welcome_email')
            
        self.assertEqual(resp.status_code, 200)
        
        logs = self._get_logs(app_id)
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0]['action'], 'Odeslán uvítací email')
        self.assertEqual(logs[0]['user'], 'admin@example.com')

if __name__ == '__main__':
    unittest.main()
