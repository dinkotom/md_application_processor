import unittest
import sys
import os
import sqlite3
import json

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app, session
from src.database import get_db_path, init_db
from src.validator import check_duplicate_contact, is_suspect_parent_email, is_valid_email
from src.parser import calculate_age

class TestValidations(unittest.TestCase):
    
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
        conn.commit()
        conn.close()
        
        # Login
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}

    def tearDown(self):
        self.ctx.pop()

    def test_duplicate_check_ignores_deleted(self):
        """Verify duplicate check IGNORES deleted records"""
        conn = sqlite3.connect(self.db_path)
        
        # 1. Create DELETED applicant with same phone/email
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, phone, membership_id, deleted)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', ('Old', 'Deleted', 'dup@example.com', '123456789', '900'))
        
        # 2. Create ACTIVE applicant with SAME phone/email
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, phone, membership_id, deleted)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', ('New', 'Active', 'dup@example.com', '123456789', '901'))
        
        active_id = conn.execute('SELECT id FROM applicants WHERE membership_id="901"').fetchone()[0]
        conn.commit()
        conn.close()
        
        # Check validation logic directly
        result = check_duplicate_contact('dup@example.com', '123456789', current_id=active_id, db_path=self.db_path)
        
        self.assertFalse(result['email_duplicate'], "Should NOT flag email duplicate against deleted record")
        self.assertFalse(result['phone_duplicate'], "Should NOT flag phone duplicate against deleted record")
        
        # Verify via API (Detail Page Alert Check)
        response = self.client.get(f'/applicant/{active_id}')
        html = response.data.decode('utf-8')
        self.assertNotIn('Nalezen duplicitní kontakt', html, "Alert should NOT be shown")

    def test_suspect_parent_email(self):
        """Verify parent email detection logic"""
        # Match (Self)
        self.assertFalse(is_suspect_parent_email('Jan', 'Novak', 'jan.novak@example.com'))
        self.assertFalse(is_suspect_parent_email('Jan', 'Novak', 'jan@example.com'))
        self.assertFalse(is_suspect_parent_email('Jan', 'Novak', 'jnovak@example.com'))
        
        # Mismatch (Parent)
        self.assertTrue(is_suspect_parent_email('Jan', 'Novak', 'petr.svoboda@example.com'))
        self.assertTrue(is_suspect_parent_email('Jan', 'Novak', 'mama123@example.com'))

    def test_age_calculation(self):
        """Verify age calculation logic"""
        from datetime import datetime
        current_year = datetime.now().year
        
        # 20 years old
        dob_20 = f"15.05.{current_year - 20}"
        self.assertEqual(calculate_age(dob_20), 20)
        
        # Invalid
        self.assertIsNone(calculate_age("invalid"))
        self.assertIsNone(calculate_age(None))

    def test_edit_email_validation(self):
        """Verify invalid email is rejected during update"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO applicants (first_name, deleted) VALUES ('Test', 0)")
        app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        
        # Try invalid email
        response = self.client.post(f'/applicant/{app_id}/update_field', 
                                   json={'field': 'email', 'value': 'not-an-email'})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid email', response.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
