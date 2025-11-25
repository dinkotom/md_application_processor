# Application Processor

A Python application that processes club membership applications received via email, generates QR codes, and creates formatted Word documents with verification checks.

## Features

- **Email Processing**: Fetches emails with subject "Nová Přihláška" from Gmail
- **Data Parsing**: Extracts applicant information (name, DOB, email, phone, membership ID)
- **QR Code Generation**: Creates QR codes with applicant details (white on dark blue)
- **Document Generation**: Produces Word documents with:
  - Applicant details
  - Age verification (warns if < 15 or ≥ 25)
  - Email-name match verification
  - Duplicate detection
  - QR code
  - Original email content
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

### 3. Set Environment Variables (Optional)

You can set environment variables to avoid entering credentials each time:

```bash
export EMAIL_USER='your-email@gmail.com'
export EMAIL_PASS='your-app-password'
```

## Running the Application

### Test Mode (Default)

```bash
python3 src/main.py
```

**Test mode behavior:**
- Uses `applications_test.db`
- Database is **cleared on each run**
- Output folder `processed_applications_test/` is **cleared**
- Emails remain **UNREAD** in Gmail (for repeated testing)
- Ideal for testing and development

### Production Mode

```bash
python3 src/main.py --production
```

**Production mode behavior:**
- Uses `applications.db`
- Records are **preserved across runs**
- Output folder `processed_applications/` **preserves existing files**
- Emails are **MARKED AS READ** after processing
- Duplicate detection works across multiple runs
- Use this for actual production processing

### Help

```bash
python3 src/main.py --help
```

### Authentication

If you haven't set environment variables, you'll be prompted to enter:
- Gmail address
- App password

### What Happens

**Test Mode:**
1. **Cleans output directory**: `processed_applications_test/` is deleted and recreated
2. **Clears test database**: `applications_test.db` is reset
3. **Fetches unread emails**: Only emails with subject "Nová Přihláška"
4. **Processes each email**:
   - Parses applicant data
   - Checks for duplicates
   - Generates QR code
   - Creates Word document
   - Stores data in database
5. **Output**: Files saved as `{ID}_{Surname}_{FirstName}.docx`

**Production Mode:**
1. **Preserves output directory**: `processed_applications/` keeps existing files
2. **Preserves database**: `applications.db` retains all records
3. **Fetches unread emails**: Only emails with subject "Nová Přihláška"
4. **Processes each email** (same as test mode)
5. **Output**: Files saved as `{ID}_{Surname}_{FirstName}.docx`

### Output

**Test Mode:**
- **Documents**: `processed_applications_test/{ID}_{Surname}_{FirstName}.docx`
- **QR Codes**: `processed_applications_test/{ID}_{Surname}_{FirstName}_qr.png`
- **Database**: `applications_test.db` (cleared on each run)

**Production Mode:**
- **Documents**: `processed_applications/{ID}_{Surname}_{FirstName}.docx`
- **QR Codes**: `processed_applications/{ID}_{Surname}_{FirstName}_qr.png`
- **Database**: `applications.db` (preserved across runs)

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
