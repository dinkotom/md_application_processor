import unittest
from unittest.mock import patch
import sys
import os
import sqlite3

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app, session
from src.database import get_db_path, init_db

class TestMembershipDuplicates(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.secret_key = 'test_secret'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        
        # Test mode
        session['mode'] = 'test'
        
        self.db_path = get_db_path()
        init_db(self.db_path)
        
        # Clean state
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM applicants')
        conn.commit()
        conn.close()
        
        # Auth
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}
            sess['mode'] = 'test'

    def tearDown(self):
        self.ctx.pop()

    @patch('src.fetcher.get_unread_emails')
    def test_duplicate_logic_by_membership_id(self, mock_get_emails):
        """
        Verify:
        1. Same Membership ID -> Duplicate (Ignored)
        2. Different Membership ID (same email) -> New (Imported)
        3. Missing Membership ID (same email) -> New (Imported)
        """
        
        conn = sqlite3.connect(self.db_path)
        
        # Setup: Existing User with ID '1234'
        email = "user@example.com"
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, membership_id, deleted, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('User', 'One', email, '1234', 0, 'Nová'))
        conn.commit()
        
        # CASE 1: Import SAME ID -> Should be DUPLICATE
        mock_body_dup = f"""
Jak se jmenuješ?: User
Jaké je tvé příjmení?: Dup
Kam ti můžeme poslat e-mail?: {email}
1234
        """
        mock_get_emails.return_value = [('msg1', mock_body_dup, '01-Jan-2025')]
        
        # Preview check
        resp1 = self.client.post('/fetch/preview')
        data1 = resp1.get_json()
        self.assertTrue(data1['emails'][0]['is_duplicate'], "Same ID '1234' should be flagged as DUPLICATE")
        self.assertEqual(data1['duplicates'], 1)

        # Confirm check (should skip)
        resp1_conf = self.client.post('/fetch/confirm')
        self.assertEqual(resp1_conf.get_json()['count'], 0, "Duplicate ID should NOT be imported")

        # CASE 2: Import DIFFERENT ID -> Should be NEW
        # Even if email is same
        mock_body_new = f"""
Jak se jmenuješ?: User
Jaké je tvé příjmení?: New
Kam ti můžeme poslat e-mail?: {email}
5678
        """
        mock_get_emails.return_value = [('msg2', mock_body_new, '02-Jan-2025')]
        
        # Preview check
        resp2 = self.client.post('/fetch/preview')
        data2 = resp2.get_json()
        self.assertFalse(data2['emails'][0]['is_duplicate'], "Different ID '5678' should include as NEW")
        self.assertEqual(data2['new'], 1)
        
        # Confirm check (should insert)
        resp2_conf = self.client.post('/fetch/confirm')
        self.assertEqual(resp2_conf.get_json()['count'], 1, "Different ID should be imported")

        # Validate DB
        count_docs = conn.execute('SELECT COUNT(*) FROM applicants').fetchone()[0]
        self.assertEqual(count_docs, 2) # Original + New ID

        # CASE 3: Import MISSING ID -> Should be ERROR (Not Imported)
        mock_body_no_id = f"""
Jak se jmenuješ?: User
Jaké je tvé příjmení?: NoID
Kam ti můžeme poslat e-mail?: {email}
        """
        mock_get_emails.return_value = [('msg3', mock_body_no_id, '03-Jan-2025')]
        
        # Preview check
        resp3 = self.client.post('/fetch/preview')
        data3 = resp3.get_json()
        self.assertFalse(data3['emails'][0]['is_duplicate'], "Missing ID should be NEW in preview")
        
        # Confirm check -> Should fail now
        resp3_conf = self.client.post('/fetch/confirm')
        data3_conf = resp3_conf.get_json()
        
        self.assertEqual(data3_conf['count'], 0, "Missing ID should NOT be imported")
        self.assertTrue(len(data3_conf['errors']) > 0, "Should return errors")
        self.assertIn("Chybí členské číslo", data3_conf['errors'][0])
        
        conn.close()

if __name__ == '__main__':
    unittest.main()
