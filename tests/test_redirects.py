
import unittest
import sys
import os
import sqlite3
from io import BytesIO
from urllib.parse import unquote

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import app
from src.database import get_db_connection

class TestRedirects(unittest.TestCase):
    
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-key'
        self.client = app.test_client()
        
        # Setup temporary test database
        self.db_path = 'test_redirects.db'
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Initialize database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Schema for applicants
        cursor.execute('''
            CREATE TABLE applicants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                status TEXT,
                deleted INTEGER DEFAULT 0,
                newsletter INTEGER DEFAULT 0,
                email_sent INTEGER DEFAULT 0,
                phone_warning_dismissed INTEGER DEFAULT 0,
                parent_email_warning_dismissed INTEGER DEFAULT 0,
                duplicate_warning_dismissed INTEGER DEFAULT 0,
                exported_to_ecomail INTEGER DEFAULT 0
            )
        ''')
        
        # Schema for audit_logs
        cursor.execute('''
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id INTEGER,
                action TEXT,
                user TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT INTO applicants (first_name, last_name, email, status)
            VALUES (?, ?, ?, ?)
        ''', ('Test', 'User', 'test@example.com', 'Nová'))
        
        conn.commit()
        conn.close()
        
        # Patch get_db_path using unittest.mock
        from unittest.mock import patch
        self.db_patcher = patch('src.database.get_db_path', return_value=self.db_path)
        self.db_patcher.start()
        
        # Simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'tester@example.com', 'name': 'Tester'}

    def tearDown(self):
        self.db_patcher.stop()
        if os.path.exists(self.db_path):
           os.remove(self.db_path)

    def test_status_update_redirect(self):
        """Test status update redirect with 'next' parameter"""
        # Test with next parameter
        target_url = '/?page=2&search=foo'
        response = self.client.post('/applicant/1/status', data={
            'status': 'Vyřízená',
            'next': target_url
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, target_url)

    def test_delete_redirect(self):
        """Test delete redirect with 'next' parameter"""
        target_url = '/?page=3&status=Nová'
        response = self.client.post('/applicant/1/delete', data={
            'next': target_url
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(unquote(response.location), target_url)
        
    def test_status_update_fallback(self):
        """Test fallback to index if next is missing"""
        response = self.client.post('/applicant/1/status', data={
            'status': 'Vyřízená'
        })
        self.assertEqual(response.status_code, 302)
        # Should contain / (index)
        self.assertTrue(response.location.endswith('/') or 'applicants' in response.location)

if __name__ == '__main__':
    unittest.main()
