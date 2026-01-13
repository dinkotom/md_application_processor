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

    # 2. Safety Check & Auto-Switch
    try:
        page.get_by_text("TEST", exact=True).wait_for(state="visible", timeout=2000)
    except Exception:
        print("TEST badge not found. Attempting to switch to TEST mode...")
        # Go to advanced settings to switch
        page.goto("/advanced")
        
        # Look for the switch button. 
        # Note: The text is "Přepnout na TEST" in advanced.html
        switch_btn = page.get_by_role("link", name="Přepnout na TEST")
        
        if switch_btn.is_visible():
            switch_btn.click()
            # Wait for the switch to happen (redirects back to advanced usually)
            page.wait_for_load_state("networkidle")
            print("Switched to TEST mode.")
        else:
            # Maybe we are in production but the button isn't there? 
            # Or maybe we are in TEST but the badge detection failed?
            # Let's check if we see "Přepnout na PRODUKCI" which implies we ARE in test
            if page.get_by_role("link", name="Přepnout na PRODUKCI").is_visible():
                print("We seem to be in TEST mode already (switch to PROD is visible).")
            else:
                 pytest.exit("CRITICAL: Could not switch to TEST mode via /advanced. Aborting.")

    # Final verification
    try:
        # Check navbar badge again
        expect(page.get_by_text("TEST", exact=True)).to_be_visible(timeout=5000)
    except AssertionError:
         pytest.exit("CRITICAL: 'TEST' badge not found even after switching! Aborting.")

    # 3. Persist Auth State
    # Save cookies to file so next run skips login
    page.context.storage_state(path="auth.json")

    return page

@pytest.fixture(autouse=True)
def clean_database(ensure_test_environment: Page):
    """
    Rule: Always start with a clean TEST database.
    This runs automatically before every test.
    """
    # We use the UI to clear the database to simulate a user action? 
    # Or better, we use an API call (via page.request) for speed.
    # However, the clear DB endpoint requires a POST.
    
    # Using API Context to speed this up
    response = ensure_test_environment.request.post(f"{BASE_URL}/clear_database")
    
    # The endpoint returns a redirect (302) to /advanced.
    # We can assume if it returns 200 or 302 it worked, but let's check.
    if response.status not in [200, 302]:
        pytest.exit(f"Failed to clean database! Status: {response.status}")
    
    # Reload page to reflect empty state if we are already on a page that shows data
    # (Though usually tests start with navigation)
    
    return response
