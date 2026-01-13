# End-to-End (E2E) Testing Guide

This directory contains the End-to-End test suite for the Application Processor, built using **Playwright** and **pytest**.

These tests simulate real user interactions in a browser to ensure critical flows (Search, Export, Database Management) work as expected.

## 📜 Rules & Guidelines
Please refer to [RULES.md](RULES.md) for safety rules, extension guidelines, and debugging tips.

## 🚀 Getting Started

### Prerequisites
1.  **Environment**: Ensure `playwright` is installed:
    ```bash
    pip install pytest-playwright
    playwright install chromium
    ```
2.  **Application**: The application must be running locally or on a accessible testing URL (e.g. `https://md-dinkotom.pythonanywhere.com/`).
3.  **Config**: The base URL is configured in `pytest.ini` or passed via command line.
4.  **Auth**: The first time you run tests, you might need to log in interactively if `auth.json` is missing or expired. The test will pause and ask you to log in.

### Running Tests

Run all E2E tests:
```bash
pytest tests/e2e/ --headed
```
*`--headed` runs the browser in visible mode. Omit it for headless mode (faster/CI).*

Run a specific test file:
```bash
pytest tests/e2e/test_export_presets.py --headed
```

## 📂 Test Suite Structure

| File | Purpose |
|------|---------|
| `conftest.py` | **Core Setup**. Defines fixtures for Auth, Clean Database, and Environment Checks. |
| `data_gen.py` | **Data Factory**. Generates random valid applicants with Czech diacritics. |
| `test_reset_db.py` | Verifies the "Clear Database" button works and UI reflects an empty state. |
| `test_search_filters.py` | Tests search (diacritics insensitive) and status status filters. |
| `test_export_presets.py` | Verifies creating, loading, and deleting export templates. |
| `test_pagination.py` | Ensures pagination controls appear at top & bottom and navigation works. |
| `test_applicant_actions.py` | Tests applicant lifecycle: Detail, Inline Edit, Notes, and Delete. |
| `test_alerts_management.py` | Verifies import of invalid data (Age, Email, Duplicates) and the "Only with alerts" filter. |

