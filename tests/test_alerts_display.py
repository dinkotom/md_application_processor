import unittest
import sys
import os
import sqlite3

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app, session
from src.database import get_db_path, init_db

class TestAlertsDisplay(unittest.TestCase):
    
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

    def test_duplicate_alert_on_detail_page(self):
        """Test that duplicate warning appears on detail page"""
        conn = sqlite3.connect(self.db_path)
        
        # 1. Create first applicant
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, phone, membership_id, deleted)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', ('Jan', 'Novak', 'jan@example.com', '123456789', '100'))
        
        # 2. Create second applicant (DUPLICATE PHONE)
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, phone, membership_id, deleted)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', ('Petr', 'Svoboda', 'petr@example.com', '123456789', '101'))
        
        # Get ID of second applicant
        dup_id = conn.execute('SELECT id FROM applicants WHERE membership_id="101"').fetchone()[0]
        conn.commit()
        conn.close()
        
        # 3. Request Detail Page
        response = self.client.get(f'/applicant/{dup_id}')
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify Alert Presence
        html = response.data.decode('utf-8')
        self.assertIn('Nalezen duplicitní kontakt', html, "Duplicate alert missing from detail page")
        self.assertIn('shodný telefon', html, "Specific duplicate reason missing")

    def test_suspect_email_alert_on_detail_page(self):
        """Test that suspect email warning appears on detail page"""
        conn = sqlite3.connect(self.db_path)
        
        # Create applicant with suspect email (Name: Jan, Email: martina@...)
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, membership_id, deleted)
            VALUES (?, ?, ?, ?, 0)
        ''', ('Jan', 'Novak', 'martina.dvorakova@example.com', '200'))
        
        suspect_id = conn.execute('SELECT id FROM applicants WHERE membership_id="200"').fetchone()[0]
        conn.commit()
        conn.close()
        
        # Request Detail Page
        response = self.client.get(f'/applicant/{suspect_id}')
        self.assertEqual(response.status_code, 200)
        
        html = response.data.decode('utf-8')
        self.assertIn('Email neobsahuje jméno uchazeče', html, "Suspect email alert missing from detail page")

    def test_invalid_formats_alerts(self):
        """Test invalid email/phone alerts and dismissal"""
        conn = sqlite3.connect(self.db_path)
        
        # Create applicant with invalid email and phone
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, phone, membership_id, deleted)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', ('Bad', 'Format', 'invalid-email', '123', '300'))
        
        app_id = conn.execute('SELECT id FROM applicants WHERE membership_id="300"').fetchone()[0]
        conn.commit()
        conn.close()
        
        # 1. Verify Alerts Present
        response = self.client.get(f'/applicant/{app_id}')
        html = response.data.decode('utf-8')
        
        self.assertIn('Neplatný formát emailu', html)
        self.assertIn('Neplatný formát telefonního čísla', html)
        
        # 2. Verify Dismiss Button logic (Phone YES)
        self.assertIn(f'action="/applicant/{app_id}/dismiss-phone-warning"', html)
        
        # 3. Dismiss Phone Warning
        response = self.client.post(f'/applicant/{app_id}/dismiss-phone-warning', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify Phone Alert Gone, Email Alert Stays
        html = response.data.decode('utf-8')
        self.assertNotIn('Neplatný formát telefonního čísla', html)
        self.assertIn('Neplatný formát emailu', html)

if __name__ == '__main__':
    unittest.main()
