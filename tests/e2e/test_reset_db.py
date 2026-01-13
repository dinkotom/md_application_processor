from playwright.sync_api import Page, expect

def test_clear_database(page: Page):
    """
    Test ensuring the database can be cleared from the Advanced settings.
    1. Navigate to /advanced
    2. Click 'Smazat testovací databázi'
    3. Confirm in Modal
    4. Verify success (empty table on index)
    """
    # 1. Go to Advanced Settings
    page.goto("/advanced")
    
    # 2. Locate the Delete Button
    # It should be visible if we are in TEST mode (guaranteed by conftest)
    # Using explicit ID for reliability
    delete_btn = page.locator("#clearDbButton")
    expect(delete_btn).to_be_visible()
    
    # 3. Click it and wait for modal
    delete_btn.click()
    modal = page.locator("#clearDbModal")
    expect(modal).to_be_visible()
    
    # 4. Confirm deletion
    # The confirmation button inside the modal
    confirm_btn = modal.locator("#confirmClearDbBtn")
    confirm_btn.click()
    
    # 5. Wait for navigation/reload (it redirects to advanced usually, but let's go to index to verify)
    # The backend redirects to 'settings.advanced' after clearing.
    # We wait for that reload.
    page.wait_for_load_state("networkidle")
    
    # 6. Verify Database is Empty
    page.goto("/")
    
    # Check for the "No records" row
    no_records = page.get_by_text("Žádné záznamy nenalezeny")
    expect(no_records).to_be_visible()
    
    # Double check: Pagination should not exist or say 0
    expect(page.get_by_text("Celkem: 0 záznamů")).to_be_visible()
