import pytest
from playwright.sync_api import Page, expect
from tests.e2e.data_gen import generate_csv_content
import io
import csv

@pytest.fixture
def populate_specific_data(page: Page):
    """
    Populates the database with specific names for search testing.
    """
    # 1. Prepare CSV with specific diacritic names
    output = io.StringIO()
    fieldnames = ["id", "jmeno", "prijmeni", "email", "telefon", "datum_narozeni", "bydliste", "skola", "oblast_kultury", "povaha", "intenzita_vyuzivani", "zdroje", "kde", "volne_sdeleni", "barvy", "souhlas"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Specific test cases
    rows = [
        {"id": 1, "jmeno": "Štěpán", "prijmeni": "Novák", "email": "stepan@test.cz"},
        {"id": 2, "jmeno": "Amálie", "prijmeni": "Křížová", "email": "amalie@test.cz"},
        {"id": 3, "jmeno": "Tomáš", "prijmeni": "Dvořák", "email": "tomas@test.cz"},
    ]
    
    for row in rows:
        # Fill defaults
        full_row = {k: "N/A" for k in fieldnames}
        full_row.update(row)
        full_row["telefon"] = "123456789"
        full_row["souhlas"] = "Ano"
        writer.writerow(full_row)
        
    csv_content = output.getvalue().encode('utf-8-sig')
    
    # 2. Upload
    page.goto("/advanced")
    
    # Create file object for input
    page.set_input_files("#csvFileInput", {
        "name": "test_search.csv",
        "mimeType": "text/csv",
        "buffer": csv_content
    })
    
    # Wait for Preview Modal
    expect(page.locator("#importModal")).to_be_visible()
    
    # Click Confirm
    page.locator("#importModal .btn-primary").click()
    
    # Wait for success/redirect
    # (The app redirects to index after success)
    page.wait_for_url("**/") 

def test_search_diacritics(page: Page, populate_specific_data):
    """
    Test that search works with and without diacritics.
    """
    # 1. Search "stepan" (no diacritics) -> Should find "Štěpán"
    page.goto("/")
    page.fill("#searchInput", "stepan")
    page.click("#searchBtn")
    
    # Assert
    expect(page.get_by_text("Štěpán Novák")).to_be_visible()
    expect(page.get_by_text("Amálie Křížová")).not_to_be_visible()
    
    # 2. Search "krizova" (no diacritics) -> Should find "Křížová"
    page.fill("#searchInput", "krizova")
    page.click("#searchBtn")
    expect(page.get_by_text("Amálie Křížová")).to_be_visible()
    
    # 3. Search "Tomáš" (with diacritics) -> Should find "Tomáš"
    page.fill("#searchInput", "Tomáš")
    page.click("#searchBtn")
    expect(page.get_by_text("Tomáš Dvořák")).to_be_visible()

def test_status_filters(page: Page, populate_specific_data):
    """
    Test that status filters work.
    """
    page.goto("/")
    
    # All imported are "Nová" by default (from data_gen logic/import logic)
    # 1. Click 'Nová' filter
    page.click("#filterStatusNova")
    # Verify URL params using regex
    import re
    expect(page).to_have_url(re.compile("status=Nov%C3%A1|status=Nová"))
    
    # Verify rows are visible
    expect(page.get_by_text("Štěpán Novák")).to_be_visible()
    
    # 2. Click 'Vyřízená' filter
    page.click("#filterStatusVyrizena")
    # Should be empty
    expect(page.get_by_text("Štěpán Novák")).not_to_be_visible()
    expect(page.get_by_text("Žádné záznamy nenalezeny")).to_be_visible()
