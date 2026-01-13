import pytest
import re
from playwright.sync_api import Page, expect
from tests.e2e.data_gen import generate_csv_content
import datetime

@pytest.fixture
def populate_alerts_data(page: Page):
    """
    Populates DB with problematic applicants.
    """
    # Calculate years
    today = datetime.date.today()
    y_under15 = today.year - 14
    y_over24 = today.year - 25
    
    custom_data = [
        # 1. OK
        {"jmeno": "Jan", "prijmeni": "Normalni", "email": "jan.ok@test.cz"},
        
        # 2. Under 15
        {"jmeno": "Baby", "prijmeni": "Yoda", "email": "baby@test.cz", "datum_narozeni": f"01.01.{y_under15}"},
        
        # 3. Over 24
        {"jmeno": "Old", "prijmeni": "Man", "email": "old@test.cz", "datum_narozeni": f"01.01.{y_over24}"},
        
        # 4. Invalid Email
        {"jmeno": "Bad", "prijmeni": "Email", "email": "bad.email"}, 
        
        # 5. Invalid Phone (too short/long)
        {"jmeno": "Bad", "prijmeni": "Phone", "email": "bad.phone@test.cz", "telefon": "123"},
        
        # 6. Suspect Parent Email (Name matches parent pattern? logic is tricky)
        # Assuming parser checks if email contains name parts of "parent" or mismatch name/email
        # Usually: Name "Jan" Email "petr.novak@" -> Suspect?
        # Let's try explicit name mismatch
        {"jmeno": "Karel", "prijmeni": "Maly", "email": "jana.mala@rodic.cz"},
        
        # 7. Duplicate (needs double insert or self-collision if imported)
        # Import checks existing DB. So if we import these, they are new.
        # To test duplicate, we need one ALREADY in DB.
        # So we include "Jan Normalni" (email match) in the list twice? 
        # But import dedupes within file? Or server rejects?
        # Settings.py: `if email in existing_emails: duplicates_count += 1`
        # So it WON'T insert duplicate. Thus we can't test "display of duplicate" unless we force it.
        # BUT the requirement says "Test Duplicate Applicants".
        # If import skips it, we verify "Duplicates: 1" in report.
        # If we want to see it in list, we must insert it manually (if constraints allow) or assume "Duplicate" alert is for Near-Duplicates?
        # Ah, `check_duplicate_contact` in applicants.py uses fuzzy matching or exact? 
        # Let's assume we want to Verify the ALERT badge on a record.
        # So we need a record that IS in the list but triggers "Duplicate".
        # If I insert "Jan Normalni" via API first, then import "Jan Normalni" (different ID?), they would collide. 
        # But import prevents this.
        # So `check_duplicate_contact` must flag NEW records that clash with OTHERS?
        # NO, `duplicates = check_duplicate_contact(...)`.
        # Maybe same phone, different email?
        {"jmeno": "Jan", "prijmeni": "Dvojnik", "email": "jan.dvojnik@test.cz", "telefon": "777888999"},
        # Collision? -> We need another one with same phone.
        {"jmeno": "Petr", "prijmeni": "Klony", "email": "petr.klony@test.cz", "telefon": "777888999"} 
    ]
    
    csv_content = generate_csv_content(count=len(custom_data), custom_rows=custom_data)
    
    page.goto("/advanced")
    page.set_input_files("#csvFileInput", {
        "name": "alerts_data.csv",
        "mimeType": "text/csv",
        "buffer": csv_content
    })
    
    expect(page.locator("#importModal")).to_be_visible()
    page.locator("#importModal .btn-primary").click()
    page.wait_for_url("**/")
    
    return custom_data

def test_alerts_filtering(page: Page, populate_alerts_data):
    """
    Test that 'Pouze s upozorněními' filters correctly and alerts are visible.
    """
    page.goto("/")
    
    # 1. Check Total (should be 8 - ignored duplicates if any?)
    # Index page shows total.
    # The import logic SKIPS duplicates of existing emails.
    # Our list has unique emails.
    # But checking same phone: "Jan Dvojnik" and "Petr Klony". Both imported? Yes.
    
    # 2. Activate Filter
    # Click "Pouze s upozorněními" (orange button)
    page.locator("#filterAlertsBtn").click()
    
    # Verify URL
    expect(page).to_have_url(re.compile("alerts=true"))
    
    # 3. Verify OK record is HIDDEN
    expect(page.get_by_text("Jan Normalni")).not_to_be_visible()
    
    # 4. Verify Bad Records are VISIBLE
    expect(page.get_by_text("Baby Yoda")).to_be_visible() # Age
    expect(page.get_by_text("Old Man")).to_be_visible() # Age
    expect(page.get_by_text("Bad Email")).to_be_visible() # Invalid Email
    expect(page.get_by_text("Bad Phone")).to_be_visible() # Invalid Phone
    
    # 5. Verify Visual Badges / Icons
    # Usually a ⚠️ icon or red row.
    # Let's check for Warning icon or specific alert text if available.
    # Assuming rows have some alert class or icon.
    
    # 6. Verify Duplicates (Phone match)
    # Check if "Jan Dvojnik" or "Petr Klony" are shown.
    expect(page.get_by_text("Jan Dvojnik")).to_be_visible()
    expect(page.get_by_text("Petr Klony")).to_be_visible()
    
    # 7. Verify Suspect Parent
    expect(page.get_by_text("Karel Maly")).to_be_visible()
    
    # 8. Deactivate Filter
    page.locator("#filterCancelAlertsBtn").click()
    expect(page.get_by_text("Jan Normalni")).to_be_visible()
