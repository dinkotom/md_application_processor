import pytest
import sqlite3
import os
from src.database import init_db, get_db_connection, remove_diacritics

# Setup a temporary test database
TEST_DB = "test_search_diacritics.db"

@pytest.fixture
def db_connection():
    # Ensure fresh start
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
        
    init_db(TEST_DB)
    
    # We need to manually register the function if we are using a direct connection 
    # instead of get_db_connection mock, but let's test the actual factory
    
    # Monkeypatch get_db_path for the duration of the test if needed, 
    # but for unit testing the SQL function we can just use direct connection with our factory logic
    
    conn = sqlite3.connect(TEST_DB)
    conn.create_function("remove_diacritics", 1, remove_diacritics)
    conn.row_factory = sqlite3.Row
    
    # Seed data
    cursor = conn.cursor()
    applicants = [
        ("Berenika", "Malečková", "berenika@example.com"),
        ("Štěpánka", "Žluťoučká", "stepanka@example.com"),
        ("Řehoř", "Přespolní", "rehor@example.com"),
        ("Jan", "Novák", "jan@example.com")
    ]
    
    for fn, ln, email in applicants:
        cursor.execute("INSERT INTO applicants (first_name, last_name, email) VALUES (?, ?, ?)", (fn, ln, email))
    
    conn.commit()
    
    yield conn
    
    conn.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_remove_diacritics_function():
    assert remove_diacritics("Malečková") == "maleckova"
    assert remove_diacritics("Štěpánka") == "stepanka"
    assert remove_diacritics("Žluťoučká") == "zlutoucka"
    assert remove_diacritics("MALEČKOVÁ") == "maleckova" # Ensure it lowercases too

def test_search_exact_match(db_connection):
    cursor = db_connection.execute("SELECT * FROM applicants WHERE remove_diacritics(last_name) LIKE remove_diacritics(?)", ("Malečková",))
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0]['last_name'] == "Malečková"

def test_search_no_diacritics_input(db_connection):
    # User types "maleckova" -> should find "Malečková"
    cursor = db_connection.execute("SELECT * FROM applicants WHERE remove_diacritics(last_name) LIKE remove_diacritics(?)", ("maleckova",))
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0]['last_name'] == "Malečková"

def test_search_mixed_diacritics_input(db_connection):
    # User types "malečkova" (mixed correct/incorrect/missing accents) -> should find "Malečková"
    cursor = db_connection.execute("SELECT * FROM applicants WHERE remove_diacritics(last_name) LIKE remove_diacritics(?)", ("malečkova",))
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0]['last_name'] == "Malečková"

def test_search_partial_match(db_connection):
    # User types "alecko" -> should find "Malečková"
    search_term = "%alecko%"
    cursor = db_connection.execute("SELECT * FROM applicants WHERE remove_diacritics(last_name) LIKE remove_diacritics(?)", (search_term,))
    results = cursor.fetchall()
    assert len(results) == 1
    assert results[0]['last_name'] == "Malečková"
