# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1] - 2025-11-27

### Added
- **Email sending functionality**: Send membership cards via email with preview and confirmation
- Email template editor in Advanced section with placeholder support
- Email tracking (sent status and timestamp) in database
- TEST mode safety: all emails in test mode go to configured test address
- Email preview modal showing recipient, subject, body, and attachments
- Czech localization for all email-related features
- Changelog file and display on Advanced page

### Changed
- Updated version number from 1.0 to 1.1
- Improved table layout: removed phone number column, reduced font size
- Fixed application received date wrapping issue

### Technical
- Added `email_template` database table
- Added `email_sent` and `email_sent_at` columns to applicants table
- Created `src/email_sender.py` module for email functionality
- Added email routes: `/email/template`, `/applicant/<id>/email/preview`, `/applicant/<id>/email/send`

---

## [1.0] - 2025-11-27

### Added
- Initial release
- Web dashboard for viewing and managing applicants
- Email fetching from Gmail
- Membership card generation with QR codes
- Statistics page with filtering
- CSV import/export functionality
- Dual mode support (Test/Production databases)
- Application received date tracking and sorting
- Age-based filtering and warnings
- School and city normalization
- Duplicate detection
- Status management (Nová, Zpracovává se, Vyřízená)

### Features
- Applicant list with pagination
- Detailed applicant view
- Search and filtering capabilities
- Membership card preview and download
- Mode switching (Test/Production)
- Database management tools
