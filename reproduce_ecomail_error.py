
import os
import sys
from src.ecomail import EcomailClient
import logging
from pprint import pprint

# Setup basic logging
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()

def main():
    api_key = os.environ.get('ECOMAIL_API_KEY')
    if not api_key:
        print("Error: ECOMAIL_API_KEY not found in environment")
        return

    client = EcomailClient(api_key)
    
    # Use a dummy email for testing
    email = "antigravity_test_comma@example.com"
    
    # Test case: Tag with comma
    subscriber_data = {
        'email': email,
        'name': 'Test',
        'surname': 'User',
        'tags': ['Valid Tag', 'Invalid, Tag'] 
    }
    
    # List ID 17 is usually test list based on codebase reading
    list_id = 17 
    
    print(f"\n--- Attempting to create subscriber with invalid tag in List {list_id} ---")
    response = client.create_subscriber(list_id, subscriber_data)
    
    print("\nResponse:")
    pprint(response)
    
    if not response['success'] and response.get('error'):
         print(f"Error Message: {response['error']}")
         print(f"Details: {response.get('details')}")

if __name__ == '__main__':
    # Add root to path so src.ecomail works
    sys.path.append(os.getcwd())
    main()
