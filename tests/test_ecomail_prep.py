
import unittest
from routes.applicants import _prepare_ecomail_data

class TestEcomailPreparation(unittest.TestCase):
    def test_comma_sanitization(self):
        # Data with commas in places that become tags
        app_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'character': 'Extrovert, Něco mezi', # Now testing split behavior
            'school': 'Gymnasium, Prague 1', # School is still treated as one tag (sanitized)
            'interests': 'Reading,Hiking'
        }
        
        result = _prepare_ecomail_data(app_data)
        
        tags = result.get('tags', [])
        
        # Check that no tag contains a comma
        for tag in tags:
            self.assertNotIn(',', tag, f"Tag '{tag}' contains a comma!")
            
        # Verify specific logic
        
        # Character should be split
        self.assertIn('Extrovert', tags)
        self.assertIn('Něco mezi', tags)
        
        # School should be sanitized (replace comma with space)
        self.assertIn('Gymnasium  Prague 1', tags)
        
        # Interests should be split
        self.assertIn('Reading', tags)
        self.assertIn('Hiking', tags)

if __name__ == '__main__':
    unittest.main()
