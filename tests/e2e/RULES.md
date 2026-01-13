# E2E Testing Rules & Guidelines

## ⚠️ Safety Rules
To prevent data loss and ensure consistent results, the suite strictly enforces:
1.  **TEST Mode Only**: Tests will fail immediately if the application is not in TEST mode (indicated by the "TEST" badge).
2.  **Clean Database**: Every test starts with a clean database. The `clean_database` fixture automatically wipes data via the `/clear_database` endpoint before each run.
3.  **Artificial Data**: Tests use `data_gen.py` to generate synthetic applicants. No real PII is ever used.
4.  **No External Side Effects**: Emails are not sent (blocked by configuration or mocked).
5.  **Use ID Selectors**: Always favor specific `id` attributes over text labels or generic selectors. This ensures tests are resilient to content changes.


## 🛠️ Extending the Suite

### Adding a New Test
1.  Create a new file `tests/e2e/test_feature_name.py`.
2.  Inject the `page` fixture (and `clean_database` is auto-used).
3.  Use `page.goto("/")` to start.

Example:
```python
def test_my_feature(page):
    page.goto("/")
    page.get_by_text("My Feature").click()
    expect(page.locator("#result")).to_be_visible()
```

### Debugging
- **Status 403 on Clear DB**: Ensure you are logged in as an admin and in TEST mode.
- **Login Timeout**: Delete `auth.json` and run with `--headed` to re-login.
- **Strict Mode Violation**: Use `.first()` or more specific selectors if multiple elements match.
