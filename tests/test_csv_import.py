import unittest
import sys
import os
import sqlite3
import csv
import io
from flask import session

# Add root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_app import app
from src.database import get_db_path, init_db

class TestCSVImport(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.secret_key = 'test_secret'
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        
        self.db_path = get_db_path()
        init_db(self.db_path)
        
        # Clean functionality
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM applicants')
        conn.commit()
        conn.close()
        
        # Login
        with self.client.session_transaction() as sess:
            sess['user'] = {'email': 'admin@example.com'}

    def tearDown(self):
        self.ctx.pop()

    def create_csv(self, headers, row_data):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row_data)
        return output.getvalue()

    def test_csv_import_variations(self):
        """Test import with different membership ID headers"""
        
        # 1. Test with 'id' (Original)
        csv_id = self.create_csv(
            ['jmeno', 'prijmeni', 'email', 'id'],
            {'jmeno': 'Jan', 'prijmeni': 'Id', 'email': 'id@test.com', 'id': '100'}
        )
        self.perform_import(csv_id, '100')
        
        # 2. Test with 'cislo_karty' (Likely missing)
        csv_card = self.create_csv(
            ['jmeno', 'prijmeni', 'email', 'cislo_karty'],
            {'jmeno': 'Jan', 'prijmeni': 'Card', 'email': 'card@test.com', 'cislo_karty': '200'}
        )
        self.perform_import(csv_card, '200')
        
        # 3. Test with 'membership_id' (English)
        csv_mem = self.create_csv(
            ['jmeno', 'prijmeni', 'email', 'membership_id'],
            {'jmeno': 'Jan', 'prijmeni': 'Mem', 'email': 'mem@test.com', 'membership_id': '300'}
        )
        self.perform_import(csv_mem, '300')

    def test_full_csv_import(self):
        """Test import of ALL fields using 'utf-8-sig' to handle BOM"""
        
        headers = [
            'jmeno', 'prijmeni', 'email', 'telefon', 'datum_narozeni', 
            'id', 'bydliste', 'skola', 'oblast_kultury', 'povaha', 
            'intenzita_vyuzivani', 'zdroje', 'kde', 'volne_sdeleni', 'barvy'
        ]
        
        row_data = {
            'jmeno': 'Kompletní',
            'prijmeni': 'Uchazeč',
            'email': 'full@example.com',
            'telefon': '777666555',
            'datum_narozeni': '01.01.2000',
            'id': '999',
            'bydliste': 'Praha',
            'skola': 'VŠB',
            'oblast_kultury': 'Hudba, Divadlo',
            'povaha': 'Introvert',
            'intenzita_vyuzivani': '5',
            'zdroje': 'Internet',
            'kde': 'Facebook',
            'volne_sdeleni': 'Poznámka',
            'barvy': 'Modrá'
        }
        
        # Manually create CSV content with BOM to verify encoding handling
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row_data)
        content_with_bom = '\ufeff' + output.getvalue()
        
        # 1. Preview
        # We need to send bytes to simulate file upload
        data = {'csv_file': (io.BytesIO(content_with_bom.encode('utf-8')), 'test_bom.csv')}
        resp = self.client.post('/import/preview', data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        
        # 2. Confirm
        with self.client.session_transaction() as sess:
            path = f"/tmp/import_{sess['user'].get('email')}.csv"
            # Write with BOM to disk
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content_with_bom)
            sess['import_file_path'] = path

        resp_conf = self.client.post('/import/confirm')
        self.assertEqual(resp_conf.status_code, 200)
        
        # 3. Verify ALL fields in DB
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT * FROM applicants WHERE membership_id = ?', ('999',)).fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row['first_name'], 'Kompletní')
        self.assertEqual(row['last_name'], 'Uchazeč')
        self.assertEqual(row['email'], 'full@example.com')
        self.assertEqual(row['phone'], '777666555')
        self.assertEqual(row['dob'], '01.01.2000')
        self.assertEqual(row['city'], 'Praha')
        self.assertEqual(row['school'], 'VŠB')
        self.assertEqual(row['interests'], 'Hudba, Divadlo')
        self.assertEqual(row['character'], 'Introvert')
        self.assertEqual(row['frequency'], '5')
        self.assertEqual(row['source'], 'Internet')
        self.assertEqual(row['source_detail'], 'Facebook')
        self.assertEqual(row['message'], 'Poznámka')
        self.assertEqual(row['color'], 'Modrá')

    def perform_import(self, csv_content, expected_id):
        # 1. Preview
        data = {'csv_file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')}
        resp = self.client.post('/import/preview', data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        
        # 2. Confirm
        with self.client.session_transaction() as sess:
            # Mock the file path as the route expects it on disk
            path = f"/tmp/import_{sess['user'].get('email')}.csv"
            with open(path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            sess['import_file_path'] = path

        resp_conf = self.client.post('/import/confirm')
        self.assertEqual(resp_conf.status_code, 200, f"Import failed for ID {expected_id}")
        
        # 3. Verify DB
        conn = sqlite3.connect(self.db_path)
        row = conn.execute('SELECT membership_id FROM applicants WHERE membership_id = ?', (expected_id,)).fetchone()
        conn.close()
        
        self.assertIsNotNone(row, f"Membership ID {expected_id} NOT imported! Headers likely not recognized.")

if __name__ == '__main__':
    unittest.main()
