# Application Processor

A Python web application for managing club membership applications. It automates the process of fetching applications from email, parsing data, checking for duplicates, and generating membership cards.

## Features

- **Web Dashboard**: User-friendly interface to manage applicants.
- **Email Processing**: Fetches emails with subject "Nová Přihláška" from Gmail.
- **Email Sending**: Sends membership cards via email with customizable templates and previews.
- **Data Parsing**: Automatically extracts applicant details (name, DOB, email, phone, etc.).
- **Duplicate Detection**: Checks for existing applicants based on name and email.
- **Membership Cards**: Generates printable PNG membership cards with QR codes.
- **Statistics**: Visualizes applicant demographics (age, city, school, interests).
- **Filtering**: Advanced filtering by status, age group, city, and school.
- **Import/Export**: Supports CSV import and Ecomail export.
- **Dual Modes**: Separate Test and Production environments.
- **Changelog**: View version history directly in the application.
- **Logging**: Comprehensive application logging for troubleshooting.

## Prerequisites

- Python 3.11 or higher
- Gmail account with App Password enabled

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repository-url>
    cd md_application_processor
    ```

2.  **Install dependencies**:
    ```bash
    pip3 install -r requirements.txt
    ```

3.  **Run Migrations**:
    Ensure your database schema is up to date by running the migration script. This applies to both new installations and updates.
    ```bash
    python3 migrate_all.py
    ```

4.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```bash
    EMAIL_USER='your-email@gmail.com'
    EMAIL_PASS='your-app-password'
    SECRET_KEY='your-secret-key-change-in-production'
    ```

    > **Note**: To generate a Gmail App Password, go to Google Account > Security > 2-Step Verification > App passwords.

## Usage

### Starting the Application

You can start the application using the provided helper script:

```bash
./start_app.sh
```

Or run it directly with Python:

```bash
python3 web_app.py
```

The application will be accessible at `http://localhost:5000`.

### Operating Modes

The application supports two modes, which can be switched via the "Advanced" tab in the web interface:

-   **Test Mode (Default)**: Uses `applications_test.db`. Ideal for testing and development. Data may be cleared easily. Emails are redirected to a test address.
-   **Production Mode**: Uses `applications.db`. Intended for actual applicant data.

## Project Structure

```
md_application_processor/
├── web_app.py              # Main Flask application
├── src/
│   ├── fetcher.py          # Email fetching logic
│   ├── parser.py           # Email and CSV parsing
│   ├── generator.py        # Membership card and QR generation
│   ├── validator.py        # Data validation and duplicate checking
│   ├── email_sender.py     # Email sending logic
│   ├── changelog.py        # Changelog reader
│   └── ecomail.py          # Ecomail integration
├── templates/              # HTML templates
├── static/                 # CSS and assets
├── applications.db         # Production database
├── applications_test.db    # Test database
├── app.log                 # Application log file
└── requirements.txt        # Python dependencies
```

## Troubleshooting

-   **No emails found**: Ensure emails have the exact subject "Nová Přihláška" and are marked as **unread** in Gmail.
-   **Authentication failed**: Verify your `EMAIL_USER` and `EMAIL_PASS` in the `.env` file.
-   **Database locked**: Ensure no other process (like an open SQLite browser) is holding a lock on the database file.

## Version

Current Version: **1.7.4**
