from playwright.sync_api import Page, expect

def test_environment_is_safe(page: Page):
    """
    Simple smoke test to verify we can connect and the safety fixture passes.
    """
    # page.goto("/") is already called by the autouse fixture 'ensure_test_environment'
    
    # We can explicitly assert the TEST badge again for clarity.
    expect(page.get_by_text("TEST", exact=True)).to_be_visible()
    
    # Verify title contains the app name
    expect(page).to_have_title("Přihlášky - Mladý divák")
