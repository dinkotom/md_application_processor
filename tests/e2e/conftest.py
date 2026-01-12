import pytest
from playwright.sync_api import Page, expect
import os

# Base URL for the production test environment
BASE_URL = "https://md-dinkotom.pythonanywhere.com"

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    context_args = {
        **browser_context_args,
        "base_url": BASE_URL,
        "viewport": {"width": 1280, "height": 720},
    }
    # Load auth state if it exists to avoid repeated logins
    if os.path.exists("auth.json"):
        context_args["storage_state"] = "auth.json"
    return context_args

@pytest.fixture(scope="function", autouse=True)
def ensure_test_environment(page: Page):
    """
    Global fixture to ensure we are running against a TEST environment.
    This runs automatically before every test.
    """
    # 1. Verification Logic
    page.goto("/")
    
    # Check if we are redirected to login
    if "google.com" in page.url or "accounts.google.com" in page.url or "login" in page.url:
        print("\n!!! PLEASE LOG IN MANUALLY IN THE BROWSER (You have 2 minutes) !!!")
        try:
            # Wait for user to complete login and return to the app
            page.wait_for_url(lambda url: BASE_URL in url and "google.com" not in url, timeout=120000)
            print("Login detected! Saving state...")
        except Exception:
            pytest.exit("Login timed out. Please run the test again and log in faster.")

    # 2. Safety Check
    # We must be on the app now. Check for TEST badge.
    try:
        test_badge = page.get_by_text("TEST", exact=True)
        # Verify it's visible with a short timeout (we should be loaded now)
        expect(test_badge).to_be_visible(timeout=5000)
    except AssertionError:
         pytest.exit("CRITICAL: 'TEST' badge not found! Are you on the correct TEST environment? Aborting.")

    # 3. Persist Auth State
    # Save cookies to file so next run skips login
    page.context.storage_state(path="auth.json")
