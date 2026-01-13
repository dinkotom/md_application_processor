import pytest
from playwright.sync_api import Page, expect
from tests.e2e.data_gen import generate_csv_content

@pytest.fixture
def populate_pagination_data(page: Page):
    """
    Populates DB with enough records (50) to force pagination.
    """
    csv_content = generate_csv_content(count=50)
    
    page.goto("/advanced")
    page.set_input_files("#csvFileInput", {
        "name": "pagination_data.csv",
        "mimeType": "text/csv",
        "buffer": csv_content
    })
    
    # Wait for modal and confirm
    expect(page.locator("#importModal")).to_be_visible()
    page.locator("#importModal .btn-primary").click()
    page.wait_for_url("**/")

def test_pagination_duplication(page: Page, populate_pagination_data):
    """
    Test that pagination controls appear at both TOP and BOTTOM of the list.
    """
    page.goto("/")
    
    # 1. Verify Pagination exists twice
    # Template uses <div class="pagination" id="paginationTop"> and <div class="pagination" id="paginationBottom">
    paginations = page.locator(".pagination")
    
    # Assert we have at least 2 (Top and Bottom)
    count = paginations.count()
    if count < 2:
        pytest.fail(f"Expected 2 pagination blocks, found {count}. (Check selector or page size)")
        
    # 2. Test Interaction with TOP pagination
    # Get the FIRST pagination block (Top)
    top_pagination = page.locator("#paginationTop")
    
    # Check it is visible
    expect(top_pagination).to_be_visible()
    
    # Click 'Next' (Další stránka)
    # The arrows are links with title="Další stránka"
    next_page_btn = top_pagination.get_by_title("Další stránka")
    
    if not next_page_btn.is_visible():
        # If disabled (only 1 page), we can't test navigation.
        # But we imported 50 items, so with per_page 20 -> 3 pages.
        pytest.fail("Next page button not visible/enabled!")
        
    next_page_btn.click()
    
    # 3. Verify URL and Content
    import re
    expect(page).to_have_url(re.compile(r"page=2"))
    
    # Content check: 
    # With 50 items (IDs 1-50), page 1 has 1-20, page 2 has 21-40? (depending on sort)
    # Default sort desc ID?
    # Let's just ensure we are on page 2.
    
    # Also verify BOTTOM pagination is present on page 2
    expect(page.locator("#paginationBottom")).to_be_visible()
