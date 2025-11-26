# Application Processor

A Python web application that processes club membership applications received via email, generates QR codes, and manages applicant data.

## Features

- **Email Processing**: Fetches emails with subject "Nová Přihláška" from Gmail
- **Data Parsing**: Extracts applicant information (name, DOB, email, phone, membership ID)
- **QR Code Generation**: Creates QR codes with applicant details (used on membership cards)
- **Membership Card Generation**: Generates printable membership cards
- **Web Dashboard**:
  - View all applicants
  - Filter by status, age, city, school
  - View statistics
  - Export to Ecomail
- **Database Storage**: SQLite database for duplicate checking and record keeping

## Prerequisites

- Python 3.10 or higher
- Gmail account with App Password enabled

## Setup

### 1. Install Dependencies

```bash
cd /Users/tomas.dinkov/Desktop/md_application_processor
pip3 install -r requirements.txt
```

### 2. Configure Gmail App Password

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Scroll to "App passwords"
4. Generate a new app password for "Mail"
5. Save the 16-character password

### 3. Set Environment Variables

Create a `.env` file:

```bash
EMAIL_USER='your-email@gmail.com'
EMAIL_PASS='your-app-password'
SECRET_KEY='your-secret-key'
```

## Running the Application

### Web Dashboard

```bash
python3 web_app.py
```

Open http://localhost:5000 in your browser.

## Database

The application uses SQLite databases with two operating modes:

### Test Mode (Default)
- **Database**: `applications_test.db`
- **Behavior**: Cleared on each run
- **Use case**: Testing, development, repeated runs on same emails

### Production Mode (--production flag)
- **Database**: `applications.db`
- **Behavior**: Records preserved across runs
- **Use case**: Actual production processing, building historical database

### Viewing Database Records

**Test database:**
```bash
sqlite3 applications_test.db "SELECT * FROM applicants;"
```

**Production database:**
```bash
sqlite3 applications.db "SELECT * FROM applicants;"
```

### Database Schema

```sql
CREATE TABLE applicants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    dob TEXT,
    membership_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(first_name, last_name, email)
);
```

## Verification Checks

### Age Check
- **Warning**: Displayed if applicant is under 15 or 25 and older
- **Format**: "⚠️ POZOR: Uchazeč má X let."

### Email-Name Match
- **Warning**: Displayed if last name doesn't appear in email address
- **Format**: "⚠️ POZOR: Email neodpovídá jménu."

### Duplicate Check
- **Warning**: Displayed if same email + name combination exists
- **Format**: "⚠️ POZOR: Duplicitní přihláška."

## Project Structure

```
md_application_processor/
├── src/
│   ├── __init__.py
│   ├── main.py           # Main application entry point
│   ├── fetcher.py        # Email fetching via IMAP
│   ├── parser.py         # Email content parsing
│   ├── generator.py      # QR code & document generation
│   └── validator.py      # Duplicate checking & database
├── processed_applications/  # Output directory
├── applications_test.db     # Test database
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Troubleshooting

### "No unread emails found"
- Check that emails have subject "Nová Přihláška"
- Verify emails are unread in Gmail
- Ensure IMAP is enabled in Gmail settings

### Authentication Error
- Verify App Password is correct (16 characters, no spaces)
- Check that 2-Step Verification is enabled
- Try generating a new App Password

### Import Errors
- Ensure all dependencies are installed: `pip3 install -r requirements.txt`
- Verify Python version: `python3 --version` (should be 3.10+)

## Notes

- **Email Status**: Emails remain **unread** in Gmail after processing (uses `BODY.PEEK[]`)
- **Test Mode**: Current configuration uses `applications_test.db` and clears it on each run
- **Production Mode**: To preserve records across runs, modify `src/main.py` to use `applications.db` without clearing

## Support

For issues or questions, refer to the implementation plan and task documents in the `.gemini` directory.
```
