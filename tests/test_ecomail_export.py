import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import sqlite3
from datetime import datetime

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app, session
from src.database import get_db_path, init_db
from src.ecomail import EcomailClient

class TestEcomailExport(unittest.TestCase):
    
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
        
        # Set Env
        os.environ['ECOMAIL_API_KEY'] = 'test_key'
        
        # Create default applicant for tests
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applicants (
                first_name, last_name, email, phone, dob, 
                membership_id, city, school, interests, character, 
                newsletter, deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Test', 'User', 'test@example.com', '+420 123 456 789', '01.01.2000',
            '1001', 'Test City', 'Test School', 'Theater', 'Actor',
            1, 0
        ))
        self.applicant_id = cursor.lastrowid
        conn.commit()
        conn.close()

    def tearDown(self):
        self.ctx.pop()

    @patch('src.ecomail.requests')
    def test_export_new_subscriber(self, mock_requests):
        """Test export of NEW subscriber sets status"""
        # Mock get_subscriber -> Not Found
        mock_requests.get.return_value.status_code = 404
        
        # Mock create_list call (post to /subscribe)
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {'success': True}

        # Setup Applicant (Newsletter = 1)
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, newsletter, deleted)
            VALUES ('New', 'User', 'new@example.com', 1, 0)
        ''')
        app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        
        # Call Export
        resp = self.client.post(f'/applicant/{app_id}/export_to_ecomail')
        
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()['success'])
        
        # Verify POST payload
        # Find the call to subscribe
        calls = [c for c in mock_requests.post.call_args_list if '/subscribe' in c[0][0]]
        self.assertTrue(len(calls) > 0)
        
        payload = calls[0][1]['json']
        subscriber_data = payload.get('subscriber_data', {})
        
        # Verify Tags include School
        tags = subscriber_data.get('tags', [])
        # Since applicant has no school defined in insert, tags might be empty or missing depending on defaults.
        # But for this test I want to verify structure.
        
        # Verify custom_fields only has MEMBERSHIP_ID
        custom_fields = subscriber_data.get('custom_fields', {})
        self.assertIn('MEMBERSHIP_ID', custom_fields)
        self.assertNotIn('SCHOOL', custom_fields)
        self.assertNotIn('STATUS', custom_fields)
        self.assertNotIn('CHARACTER', custom_fields) # Should be in tags
        self.assertEqual(len(custom_fields), 1, "Only MEMBERSHIP_ID should be in custom_fields")
        
        # New user -> Status should be set (1 for subscribed)
        self.assertIn('status', subscriber_data)
        self.assertEqual(subscriber_data['status'], 1)

    def test_payload_content(self):
        """Test exact content of tags and fields"""
        # Mock requests
        with patch('src.ecomail.requests') as mock_requests:
            mock_requests.get.return_value.status_code = 404 # New user
            mock_requests.post.return_value.status_code = 200
            mock_requests.post.return_value.json.return_value = {'success': True}
            
            # Create applicant with full data
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO applicants (
                    first_name, last_name, email, school, character, interests, membership_id, deleted
                ) VALUES (
                    'Tag', 'Tester', 'tags@example.com', 'My School', 'Kind', 'Code, Music', '999', 0
                )
            ''')
            app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            conn.close()
            
            client = self.app.test_client()
            with client.session_transaction() as sess:
                sess['user'] = {'email': 'admin@test.com'}
                
            client.post(f'/applicant/{app_id}/export_to_ecomail')
            
            # Check Payload
            call_args = mock_requests.post.call_args
            payload = call_args.kwargs['json']
            
            # Tags are popped from subscriber_data and moved to top level by EcomailClient
            tags = payload.get('tags', [])
            sub = payload['subscriber_data']
            
            self.assertIn('My School', tags)
            self.assertIn('Kind', tags)
            self.assertIn('Code', tags)
            self.assertIn('Music', tags)
            
            cf = sub['custom_fields']
            self.assertEqual(cf['MEMBERSHIP_ID'], '999')
            self.assertEqual(len(cf), 1)

    @patch('src.ecomail.requests')
    def test_export_existing_subscriber_update(self, mock_requests):
        """Test export of EXISTING subscriber DOES NOT update status"""
        # Mock get_subscriber -> Found
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {'id': 123, 'email': 'existing@example.com', 'status': 2} # Unsubscribed in Ecomail
        
        mock_requests.get.side_effect = lambda url, **kwargs: mock_get_resp if '/subscribers/' in url else MagicMock(status_code=200)

        # Mock update call
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {'success': True}

        # Setup Applicant (Newsletter = 1 in our DB, trying to overwrite Ecomail's Unsubscribed status?)
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO applicants (first_name, last_name, email, newsletter, deleted)
            VALUES ('Existing', 'User', 'existing@example.com', 1, 0)
        ''')
        app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        
        # Call Export
        resp = self.client.post(f'/applicant/{app_id}/export_to_ecomail')
        
        self.assertEqual(resp.status_code, 200)
        
        # Verify POST payload
        calls = [c for c in mock_requests.post.call_args_list if '/subscribe' in c[0][0]]
        payload = calls[0][1]['json']
        subscriber_data = payload.get('subscriber_data', {})
        
        # Existing user -> Status should NOT be in subscriber_data (preserved)
        # Or if it is, verify logic. EcomailClient.create_subscriber logic says:
        # if not is_update ... set status.
        # Since is_update is True, it should skip setting status.
        self.assertNotIn('status', subscriber_data, "Status should NOT be sent for existing subscriber update")
        self.assertFalse(payload.get('resubscribe'), "Resubscribe should be False for update")

    @patch('routes.applicants.get_db_connection')
    @patch('src.ecomail.requests')
    def test_list_id_selection_production_fresh(self, mock_requests, mock_get_db):
        """Test correct List ID is used for Production mode (Fresh Client)"""
        # Configure Mock DB to point to TEST DB even if mode is production
        def get_test_conn():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        mock_get_db.side_effect = get_test_conn

        # Mock responses
        mock_requests.get.return_value.status_code = 404
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {'success': True}

        # Setup Applicant in TEST DB
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO applicants (first_name, email, deleted) VALUES ('TestProd', 'prod@example.com', 0)")
        app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        # Create FRESH client
        client = self.app.test_client()
        
        # Login and set mode
        with client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'production'
            
        resp = client.post(f'/applicant/{app_id}/export_to_ecomail')
        if resp.status_code != 200:
             print(f"DEBUG: Status {resp.status_code}, Location: {resp.headers.get('Location')}")
        self.assertEqual(resp.status_code, 200)
        
        # Verify List ID 16 used
        args, _ = mock_requests.post.call_args
        self.assertIn('/lists/16/subscribe', args[0])

    @patch('src.ecomail.requests')
    def test_list_id_selection_test_fresh(self, mock_requests):
        """Test correct List ID is used for Test mode (Fresh Client)"""
        mock_requests.get.return_value.status_code = 404
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {'success': True}

        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO applicants (first_name, email, deleted) VALUES ('TestTest', 'test@example.com', 0)")
        app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        client = self.app.test_client()
        
        with client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@test.com'}
            sess['mode'] = 'test'

        client.post(f'/applicant/{app_id}/export_to_ecomail')
        
        # Verify List ID 17 used
        args, _ = mock_requests.post.call_args
        self.assertIn('/lists/17/subscribe', args[0])

    def test_check_ecomail_new(self):
        """Test check_ecomail for new subscriber"""
        with patch('src.ecomail.requests') as mock_requests:
            # Mock get_subscriber -> 404 Not Found
            mock_requests.get.return_value.status_code = 404
            
            # Create applicant
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO applicants (first_name, last_name, email, membership_id, deleted) 
                VALUES ('Check', 'New', 'check_new@example.com', '123', 0)
            ''')
            app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            conn.close()
            
            client = self.app.test_client()
            with client.session_transaction() as sess:
                sess['user'] = {'email': 'admin@test.com'}
                
            response = client.get(f'/applicant/{app_id}/check_ecomail')
            data = response.get_json()
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['success'])
            self.assertFalse(data['exists'])
            self.assertIsNone(data['existing_data'])
            
            # Verify proposed data
            proposed = data['proposed_data']
            self.assertEqual(proposed['email'], 'check_new@example.com')
            # Custom fields key is accessed directly
            self.assertEqual(proposed['custom_fields']['MEMBERSHIP_ID'], '123')
            
            # Verify list_id (default test -> 17)
            self.assertEqual(data['list_id'], '17')

    def test_check_ecomail_existing(self):
        """Test check_ecomail for existing subscriber"""
        with patch('src.ecomail.requests') as mock_requests:
            # Mock get_subscriber -> 200 OK
            mock_requests.get.return_value.status_code = 200
            mock_requests.get.return_value.json.return_value = {
                'subscriber': {'email': 'check_exist@example.com', 'id': 99}
            }
            
            # Create applicant
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO applicants (first_name, last_name, email, membership_id, deleted) 
                VALUES ('Check', 'Exist', 'check_exist@example.com', '456', 0)
            ''')
            app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
            conn.close()
            
            client = self.app.test_client()
            with client.session_transaction() as sess:
                sess['user'] = {'email': 'admin@test.com'}
                
            response = client.get(f'/applicant/{app_id}/check_ecomail')
            data = response.get_json()
            
            self.assertTrue(data['success'])
            self.assertTrue(data['exists'])
            self.assertIsNotNone(data['existing_data'])

    @patch('src.ecomail.EcomailClient.get_subscriber')
    def test_check_ecomail_identical(self, mock_get):
        """Test that identical data returns has_changes=False"""
        # Mock existing subscriber data that MATCHES our test applicant
        mock_get.return_value = {
            'success': True,
            'data': {
                'subscriber': {
                    'email': 'test@example.com',
                    'name': 'Test',
                    'surname': 'User',
                    'phone': '+420 123 456 789', # Note: spaces are stripped in comparison, but let's match input
                    'birthday': '2000-01-01',
                    'tags': ['Actor', 'Theater', 'Test School'],
                    'custom_fields': {
                        'MEMBERSHIP_ID': '1001'
                    }
                }
            }
        }
        
        response = self.client.get(f'/applicant/{self.applicant_id}/check_ecomail')
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertTrue(data['exists'])
        self.assertFalse(data['has_changes'], "Should not have changes if data is identical")
        
        # Verify diff content
        for item in data['diff']:
            self.assertFalse(item['is_diff'], f"Field {item['label']} should not be different")

    @patch('src.ecomail.EcomailClient.get_subscriber')
    def test_check_ecomail_different(self, mock_get):
        """Test that different data returns has_changes=True"""
        # Mock existing subscriber data that is DIFFERENT
        mock_get.return_value = {
            'success': True,
            'data': {
                'subscriber': {
                    'email': 'test@example.com',
                    'name': 'OldName', # Different
                    'surname': 'User',
                    'phone': '+420123456789',
                    'tags': [], # Different
                    'custom_fields': {
                        'MEMBERSHIP_ID': '9999' # Different
                    }
                }
            }
        }
        
        response = self.client.get(f'/applicant/{self.applicant_id}/check_ecomail')
        data = response.get_json()
        
        self.assertTrue(data['success'])
        self.assertTrue(data['has_changes'], "Should have changes")
        
        # Verify specific diffs
        diff_map = {item['label']: item for item in data['diff']}
        
        self.assertTrue(diff_map['Jméno']['is_diff'])
        self.assertEqual(diff_map['Jméno']['existing'], 'OldName')
        self.assertEqual(diff_map['Jméno']['proposed'], 'Test')
        
        self.assertTrue(diff_map['Členské číslo']['is_diff'])
        self.assertEqual(diff_map['Členské číslo']['existing'], '9999')
        self.assertEqual(diff_map['Členské číslo']['proposed'], '1001')

    @patch('src.ecomail.EcomailClient.get_subscriber')
    def test_check_ecomail_membership_id_missing(self, mock_get):
        """Test detection when MEMBERSHIP_ID is missing in Ecomail"""
        mock_get.return_value = {
            'success': True,
            'data': {
                'subscriber': {
                    'email': 'test@example.com',
                    'name': 'Test',
                    'surname': 'User',
                    # No custom fields or empty
                    'custom_fields': {}
                }
            }
        }
        
        response = self.client.get(f'/applicant/{self.applicant_id}/check_ecomail')
        data = response.get_json()
        
        self.assertTrue(data['has_changes'])
        diff_map = {item['label']: item for item in data['diff']}
        
        self.assertTrue(diff_map['Členské číslo']['is_diff'])
        self.assertEqual(diff_map['Členské číslo']['existing'], '-') # Normalized empty
        self.assertEqual(diff_map['Členské číslo']['proposed'], '1001')

    @patch('src.ecomail.requests')
    def test_export_update_membership_id(self, mock_requests):
        """Test that updating validates the payload contains MEMBERSHIP_ID"""
        # Mock get_subscriber -> EXISTS
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            'success': True,
            'data': {
                'subscriber': {
                    'email': 'test@example.com',
                    'id': 123
                }
            }
        }
        
        # Mock subscribe call (update)
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {'success': True}

        # Call Export
        resp = self.client.post(f'/applicant/{self.applicant_id}/export_to_ecomail')
        
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()['success'])
        
        # Verify POST payload
        calls = [c for c in mock_requests.post.call_args_list if '/subscribe' in c[0][0]]
        self.assertTrue(len(calls) > 0)
        
        payload = calls[0][1]['json']
        subscriber_data = payload.get('subscriber_data', {})
        custom_fields = subscriber_data.get('custom_fields', {})
        
        print(f"DEBUG: Payload sent to Ecomail: {payload}")
        
        self.assertIn('MEMBERSHIP_ID', custom_fields)
        self.assertEqual(custom_fields['MEMBERSHIP_ID'], '1001')
        self.assertTrue(payload.get('update_existing'))

    @patch('src.ecomail.EcomailClient.get_subscriber')
    def test_check_ecomail_nested_fields(self, mock_get):
        """Test reading custom fields from nested lists structure"""
        # Mock data where custom_fields is empty/None but exists in lists
        mock_get.return_value = {
            'success': True,
            'data': {
                'subscriber': {
                    'email': 'test@example.com',
                    'name': 'Test',
                    'surname': 'User',
                    'phone': '+420 123 456 789',
                    'birthday': '2000-01-01',
                    'tags': ['Actor', 'Theater', 'Test School'],
                    'custom_fields': None,
                    'lists': {
                        '17': {
                            'c_fields': {
                                'MEMBERSHIP_ID': '1001'
                            },
                            'status': 1
                        }
                    }
                }
            }
        }
        
        # Test in 'test' mode (list 17)
        with self.client.session_transaction() as sess:
            sess['mode'] = 'test'
            
        response = self.client.get(f'/applicant/{self.applicant_id}/check_ecomail')
        data = response.get_json()
        
        self.assertTrue(data['success'])
        # Should be identical because 1001 matches default applicant
        self.assertFalse(data['has_changes'], "Should find nested MEMBERSHIP_ID and match")
        
        diff_map = {item['label']: item for item in data['diff']}
        self.assertFalse(diff_map['Členské číslo']['is_diff'])
        self.assertEqual(diff_map['Členské číslo']['existing'], '1001')

if __name__ == '__main__':
    unittest.main()
