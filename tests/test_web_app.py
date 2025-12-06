import unittest
import sys
import os
import sqlite3
from io import BytesIO

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_app import app, get_db_connection

class TestWebApp(unittest.TestCase):
    
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-key'
        self.client = app.test_client()
        
        # Setup temporary test database
        self.db_path = 'test_temp.db'
        
        # Initialize database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE applicants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                dob TEXT,
                membership_id TEXT,
                city TEXT,
                school TEXT,
                interests TEXT,
                character TEXT,
                frequency TEXT,
                source TEXT,
                source_detail TEXT,
                message TEXT,
                color TEXT,
                newsletter TEXT,
                full_body TEXT,
                status TEXT DEFAULT 'Nová',
                deleted INTEGER DEFAULT 0,
                exported_to_ecomail INTEGER DEFAULT 0,
                exported_at TIMESTAMP,
                application_received TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(first_name, last_name, email)
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                user TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                old_value TEXT,
                new_value TEXT,
                FOREIGN KEY (applicant_id) REFERENCES applicants (id)
            );
        ''')
        
        # Insert sample data
        cursor.execute('''
            INSERT INTO applicants (first_name, last_name, email, dob, membership_id, city, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Jan', 'Novák', 'jan.novak@example.com', '01.01.2000', '1001', 'Praha', 'Nová'))
        
        conn.commit()
        conn.close()
        
        # Patch get_db_path/connection to use our temp DB
        # Since we can't easily patch the global function in the imported module without mocking,
        # we will rely on the fact that we can override the DB path if we modify the function or 
        # use a context manager. 
        # However, web_app.py imports sqlite3 and uses a global DB_PATH_TEST.
        # Let's try to patch the get_db_path function in web_app module.
        
        import web_app
        self.original_get_db_path = web_app.get_db_path
        web_app.get_db_path = lambda: self.db_path
        
        # Simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'test@example.com', 'name': 'Test User'}

    def tearDown(self):
        # Restore original function
        import web_app
        web_app.get_db_path = self.original_get_db_path
        
        # Remove temp database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_index_page(self):
        """Test that the index page loads and shows the applicant"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Jan', response.data)
        self.assertIn(b'Nov\xc3\xa1k', response.data) # Novák in utf-8

    def test_applicant_detail(self):
        """Test that the applicant detail page loads"""
        # Get the ID of the inserted applicant (should be 1)
        response = self.client.get('/applicant/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Jan', response.data)
        self.assertIn(b'1001', response.data)

    def test_stats_page(self):
        """Test that the stats page loads"""
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Statistiky', response.data)
        self.assertIn(b'Praha', response.data)

    def test_update_status(self):
        """Test updating applicant status"""
        response = self.client.post('/applicant/1/update_status', data={
            'status': 'Vyřízená'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify change in DB
        conn = sqlite3.connect(self.db_path)
        status = conn.execute('SELECT status FROM applicants WHERE id = 1').fetchone()[0]
        conn.close()
        self.assertEqual(status, 'Vyřízená')

    def test_download_card(self):
        """Test downloading the membership card"""
        response = self.client.get('/applicant/1/card')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')

    def test_stats_with_character(self):
        """Test that stats page includes character info"""
        # Add character to the test applicant
        conn = sqlite3.connect(self.db_path)
        conn.execute('UPDATE applicants SET character = ? WHERE id = 1', ('Introvert',))
        conn.commit()
        conn.close()
        
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Povaha', response.data)
        self.assertIn(b'Introvert', response.data)

    def test_filter_by_character(self):
        """Test filtering applicants by character"""
        # Add another applicant with different character
        conn = sqlite3.connect(self.db_path)
        # Update first applicant
        conn.execute('UPDATE applicants SET character = ? WHERE id = 1', ('Introvert',))
        # Add second applicant
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, character, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Petr', 'Svoboda', 'petr@example.com', 'Extrovert', 'Nová'))
        conn.commit()
        conn.close()
        
        # Filter for Introvert
        response = self.client.get('/?character=Introvert')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Jan', response.data)
        self.assertNotIn(b'Petr', response.data)
        
        # Filter for Extrovert
        response = self.client.get('/?character=Extrovert')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Jan', response.data)
        self.assertIn(b'Petr', response.data)

    def test_pagination(self):
        """Test pagination links exist"""
        # Create enough applicants to trigger pagination (per_page=20)
        # We already have 2. Let's create dummy links check logic via template rendering if possible,
        # or just ensure page parameter works.
        conn = sqlite3.connect(self.db_path)
        for i in range(25):
            conn.execute('''
                INSERT INTO applicants (first_name, last_name, email, membership_id, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (f'User{i}', f'Test{i}', f'user{i}@test.com', f'{2000+i}', 'Nová'))
        conn.commit()
        conn.close()
        
        # Request page 2
        response = self.client.get('/?page=2')
        self.assertEqual(response.status_code, 200)
        # Should show some users from page 2 (User0, Jan, etc.)
        # With DESC sort, older users are on later pages
        self.assertIn(b'User0', response.data)
        
        # Should see pagination controls
        self.assertIn(b'pagination-numbers', response.data)
        self.assertIn(b'active', response.data) # Active page indicator

    def test_update_applicant_field(self):
        """Test updating a single applicant field via AJAX"""
        import json
        
        # Test updating first name
        response = self.client.post('/applicant/1/update_field',
            data=json.dumps({
                'field': 'first_name',
                'value': 'Updated Name'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify change in DB
        conn = sqlite3.connect(self.db_path)
        first_name = conn.execute('SELECT first_name FROM applicants WHERE id = 1').fetchone()[0]
        conn.close()
        self.assertEqual(first_name, 'Updated Name')
    
    def test_update_applicant_field_invalid(self):
        """Test updating an invalid field returns error"""
        import json
        
        response = self.client.post('/applicant/1/update_field',
            data=json.dumps({
                'field': 'invalid_field',
                'value': 'test'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Invalid field', data['error'])
    
    def test_update_applicant_dob(self):
        """Test updating date of birth field"""
        import json
        
        response = self.client.post('/applicant/1/update_field',
            data=json.dumps({
                'field': 'dob',
                'value': '15.03.2005'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify change in DB
        conn = sqlite3.connect(self.db_path)
        dob = conn.execute('SELECT dob FROM applicants WHERE id = 1').fetchone()[0]
        conn.close()
        self.assertEqual(dob, '15.03.2005')

if __name__ == '__main__':
    unittest.main()
