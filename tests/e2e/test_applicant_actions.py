import pytest
from playwright.sync_api import Page, expect
from tests.e2e.data_gen import generate_csv_content

@pytest.fixture
def populate_one_applicant(page: Page):
    """
    Populates DB with exactly 1 known applicant.
    """
    custom_data = [{
        "jmeno": "Jan",
        "prijmeni": "Testovací",
        "email": "jan.testovaci@example.test"
    }]
    csv_content = generate_csv_content(count=1, custom_rows=custom_data)
    
    page.goto("/advanced")
    page.set_input_files("#csvFileInput", {
        "name": "one_applicant.csv",
        "mimeType": "text/csv",
        "buffer": csv_content
    })
    
    expect(page.locator("#importModal")).to_be_visible()
    page.locator("#importModal .btn-primary").click()
    page.wait_for_url("**/")
    return custom_data[0]

def test_applicant_lifecycle(page: Page, populate_one_applicant):
    """
    Test full lifecycle: Detail -> Edit (Inline) -> Status Change (Inline) -> Note -> Delete.
    """
    # 1. Open Detail
    page.goto("/")
    row = page.get_by_role("row", name="Jan Testovací")
    expect(row).to_be_visible()
    row.click() 
    
    # Verify we are on detail page
    import re
    expect(page).to_have_url(re.compile(r"/applicant/"))
    expect(page.get_by_role("heading", name="Jan Testovací")).to_be_visible()
    
    # 2. Edit Applicant (Inline Email)
    # Click Edit button for email (pencil icon)
    # We can use ID selector as they seem stable in template
    page.locator("#btn_edit_email").click()
    
    # Change Email
    new_email = "jan.updated@example.test"
    page.locator("#input_email input").fill(new_email)
    page.locator("#btn_save_email").click()
    
    # Verify update (Text should be visible in display span)
    expect(page.locator("#display_email")).to_contain_text(new_email)
    
    # 3. Change Status (Inline)
    page.locator("#btn_edit_status").click()
    
    # Select "Zpracovává se"
    page.locator("#input_status select").select_option("Zpracovává se")
    page.locator("#btn_save_status").click()
    
    # Verify status changed (Badge text)
    expect(page.locator("#display_status")).to_contain_text("Zpracovává se")
    
    # 4. Add Internal Note
    note_text = "Test Note 123"
    # Note is auto-saved on blur!
    page.locator("#noteTextarea").fill(note_text)
    page.locator("#noteTextarea").blur()
    
    # Verify save status
    expect(page.locator("#noteSaveStatus")).to_contain_text("Uloženo")
    
    # Refresh to verify persistence
    page.reload()
    expect(page.locator("#noteTextarea")).to_have_value(note_text)
    
    # 5. Delete application
    # Click global delete button (opens custom modal)
    page.locator("#deleteApplicantBtn").click()
    
    # Wait for modal and confirm
    # Modal ID is deleteModal. Inside it, there is a form with submit button.
    # The submit button likely is "Smazat" or similar styled default button?
    # Let's target the button inside the modal actions.
    # The modal structure: .modal-actions -> form -> button
    # Or just use text inside modal
    delete_confirm_btn = page.locator("#confirmDeleteApplicantBtn")
    expect(delete_confirm_btn).to_be_visible()
    delete_confirm_btn.click()
    
    # Verify redirection to index
    expect(page).to_have_url(re.compile(r"/$"))
    
    # Verify applicant gone
    expect(page.get_by_text("Jan Testovací")).not_to_be_visible()
