
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
    email = "ondrackova.anezka@seznam.cz"
    
    print(f"\n--- Fetching Subscriber: {email} ---")
    response = client.get_subscriber(email)
    
    if response.get('success'):
        data = response.get('data', {})
        print("Response Keys:", data.keys())
        
        # Check structure
        # Is it { 'subscriber': { ... } } or just { ... } ?
        
        if 'subscriber' in data:
            print("Found nested 'subscriber' object.")
            sub = data['subscriber']
            print("Subscriber Keys:", sub.keys())
            print("Custom Fields (in subscriber):", sub.get('custom_fields'))
        
        # Sometimes custom_fields are at root?
        if 'custom_fields' in data:
            print("Found 'custom_fields' at root:")
            pprint(data['custom_fields'])
            
        # Full dump for certainty
        print("\n--- Full Response Data ---")
        pprint(data)
        
    else:
        print(f"Failed to get subscriber: {response.get('error')}")

if __name__ == '__main__':
    # Add root to path so src.ecomail works
    sys.path.append(os.getcwd())
    main()
