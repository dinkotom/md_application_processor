import sqlite3
import json
import os
from datetime import datetime

DB_PATH = 'applications_test.db'

def get_payload(applicant_id):
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    databases = ['applications.db', 'applications_test.db']
    
    conn = None
    row = None
    used_db = None
    
    for db in databases:
        if not os.path.exists(db): continue
        try:
             c = sqlite3.connect(db)
             c.row_factory = sqlite3.Row
             # Check ID or Membership ID
             r = c.execute("SELECT * FROM applicants WHERE id = ? OR membership_id = ?", (applicant_id, str(applicant_id))).fetchone()
             if r:
                 conn = c
                 row = r
                 used_db = db
                 break
             c.close()
        except Exception as e:
            print(f"Error checking {db}: {e}")
            
    if not row:
        print(f"Applicant ID {applicant_id} not found in {databases}")
        return

    print(f"Found Applicant {applicant_id} in {used_db}")
    
    # conn is open
    # conn.row_factory = sqlite3.Row
    
    app_data = dict(row)
    
    # Logic mirroring routes/applicants.py
    tags = []
    char = app_data.get('character')
    if char: tags.append(char)
    interests = app_data.get('interests')
    if interests:
        for i in interests.split(','):
            if i.strip(): tags.append(i.strip())
            
    school = app_data.get('school')
    if school: tags.append(school)

    subscriber_data = {
        'email': app_data.get('email'),
        'name': app_data.get('first_name', ''),
        'surname': app_data.get('last_name', ''),
        'phone': app_data.get('phone', ''),
        'city': app_data.get('city', ''),
        'tags': tags,
        'custom_fields': {
            'MEMBERSHIP_ID': app_data.get('membership_id', '')
        }
    }

    # Native Birthday
    dob = app_data.get('dob')
    if dob:
        try:
            dob_clean = dob.strip().replace('/', '.')
            dt = datetime.strptime(dob_clean, '%d.%m.%Y')
            subscriber_data['birthday'] = dt.strftime('%Y-%m-%d')
        except:
             subscriber_data['birthday'] = dob

    # Simulate final payload construction from EcomailClient
    # Note: Tags are moved to top level in EcomailClient.create_subscriber
    final_tags = subscriber_data.pop('tags', [])
    
    payload = {
        'subscriber_data': subscriber_data,
        'trigger_autoresponders': True,
        'update_existing': True,
        'resubscribe': False
    }
    
    if final_tags:
        payload['tags'] = final_tags

    print(json.dumps(payload, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    get_payload(1976)
