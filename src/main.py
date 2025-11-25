import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import getpass
import argparse
from src.fetcher import get_unread_emails
from src.parser import parse_email_body
from src.generator import generate_qr_code, generate_document

from src.validator import init_db, is_duplicate, record_applicant, clear_db
import shutil

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process club membership applications from email.')
    parser.add_argument('--production', action='store_true', 
                       help='Use production database (applications.db) and preserve records. Default: test mode (applications_test.db, cleared on each run)')
    args = parser.parse_args()
    
    # Configure database based on mode
    if args.production:
        db_path = "applications.db"
        output_dir = "processed_applications"
        mode_name = "PRODUCTION"
        print("--- Application Processor (PRODUCTION MODE) ---")
        print("⚠️  Using production database: applications.db")
        print("⚠️  Records will be PRESERVED across runs")
        print(f"⚠️  Output folder: {output_dir}/")
        print("⚠️  Emails will be MARKED AS READ after processing")
    else:
        db_path = "applications_test.db"
        output_dir = "processed_applications_test"
        mode_name = "TEST"
        print("--- Application Processor (TEST MODE) ---")
        print("ℹ️  Using test database: applications_test.db")
        print("ℹ️  Database will be CLEARED on each run")
        print(f"ℹ️  Output folder: {output_dir}/ (will be cleared)")
        print("ℹ️  Emails will remain UNREAD for repeated testing")
    
    # Credentials
    email_user = os.environ.get("EMAIL_USER")
    if not email_user:
        email_user = input("Enter Gmail Address: ")
        
    email_pass = os.environ.get("EMAIL_PASS")
    if not email_pass:
        email_pass = getpass.getpass("Enter App Password: ")
        
    print(f"Connecting to {email_user}...")
    emails = get_unread_emails(email_user, email_pass, mark_as_read=args.production)
    
    if not emails:
        print("No unread emails found.")
        return

    print(f"Found {len(emails)} unread emails. Processing...")
    
    # Clean and create output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"✓ Output directory prepared: {output_dir}/")
    
    # Initialize DB
    if args.production:
        # Production mode: create table if doesn't exist, but don't clear
        init_db(db_path)
        print(f"✓ Production database initialized")
    else:
        # Test mode: clear database on each run
        clear_db(db_path)
        print(f"✓ Test database cleared and initialized")
        
    for uid, body in emails:
        try:
            print(f"Processing Email ID: {uid}")
            # Parse
            data = parse_email_body(body)
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            email = data.get('email', '')
            
            name = f"{first_name}_{last_name}"
            print(f"Processing application for: {name}")
            
            # Duplicate Check
            duplicate = is_duplicate(first_name, last_name, email, db_path=db_path)
            if duplicate:
                print("  -> DUPLICATE DETECTED!")
            
            # Record in DB
            record_applicant(data, db_path=db_path)
            
            # Generate filenames
            mid = data.get('membership_id', '0000')
            # Ensure safe filename
            safe_mid = "".join([c for c in mid if c.isalnum()])
            safe_last = "".join([c for c in last_name if c.isalpha() or c.isdigit()]).rstrip()
            safe_first = "".join([c for c in first_name if c.isalpha() or c.isdigit()]).rstrip()
            
            filename_base = f"{safe_mid}_{safe_last}_{safe_first}"
            
            qr_path = os.path.join(output_dir, f"{filename_base}_qr.png")
            doc_path = os.path.join(output_dir, f"{filename_base}.docx")
            
            # Generate
            # generate_qr_code(data, qr_path)
            # generate_document(data, qr_path, doc_path, is_duplicate=duplicate)
            
            # print(f"  -> Saved to {doc_path}")
            print(f"  -> Processed (Document generation disabled)")
            
        except Exception as e:
            print(f"  -> Error processing email {uid}: {e}")

if __name__ == "__main__":
    main()
