import unittest
import sys
import os
from PIL import Image
from io import BytesIO

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.generator import generate_membership_card, generate_qr_code_bytes

class TestGenerator(unittest.TestCase):
    
    def setUp(self):
        self.sample_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'dob': '01/01/2000',
            'membership_id': '1234',
            'phone': '123456789'
        }

    def test_generate_qr_code_bytes(self):
        """Test that QR code generation returns valid PNG bytes"""
        img_io = generate_qr_code_bytes(self.sample_data)
        
        # Check it returns BytesIO
        self.assertIsInstance(img_io, BytesIO)
        
        # Check it's a valid image
        img_io.seek(0)
        img = Image.open(img_io)
        
        self.assertEqual(img.format, 'PNG')
        self.assertGreater(img.width, 0)
        self.assertGreater(img.height, 0)

    def test_generate_membership_card(self):
        """Test that membership card generation returns valid PNG bytes with correct dimensions"""
        img_io = generate_membership_card(self.sample_data)
        
        # Check it returns BytesIO
        self.assertIsInstance(img_io, BytesIO)
        
        # Check it's a valid image
        img_io.seek(0)
        img = Image.open(img_io)
        
        self.assertEqual(img.format, 'PNG')
        
        # Check dimensions match the template (1024x585)
        self.assertEqual(img.width, 1050)
        self.assertEqual(img.height, 600)

if __name__ == '__main__':
    unittest.main()
