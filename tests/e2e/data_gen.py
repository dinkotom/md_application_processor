import random
import io
import csv

FIRST_NAMES = ["Jan", "Petr", "Jana", "Marie", "Lucie", "Tomáš", "Jakub", "Eva", "Adam", "Veronika"]
LAST_NAMES = ["Novák", "Svoboda", "Novotná", "Dvořák", "Černá", "Procházka", "Kučera", "Veselá"]
CITIES = ["Praha", "Brno", "Ostrava", "Plzeň", "Liberec", "Olomouc"]
SCHOOLS = ["Gymnázium", "SŠ", "ZŠ", "Konzervatoř"]

def generate_applicant():
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    # Ensure Diacritics are used to test search!
    return {
        "jmeno": fn,
        "prijmeni": ln,
        "email": f"{fn.lower()}.{ln.lower()}.{random.randint(100,999)}@example.test", # .test TLD
        "telefon": f"7{random.randint(10,99)}{random.randint(100,999)}{random.randint(100,999)}",
        "datum_narozeni": f"{random.randint(1,28)}.{random.randint(1,12)}.{random.randint(2005, 2010)}",
        "bydliste": random.choice(CITIES),
        "skola": random.choice(SCHOOLS),
        "oblast_kultury": "Divadlo",
        "povaha": "Introvert",
        "intenzita_vyuzivani": "Často",
        "zdroje": "Internet",
        "kde": "Doma",
        "volne_sdeleni": "Test data",
        "barvy": "Modrá",
        "souhlas": "Ano"
    }

def generate_csv_content(count=5, custom_rows=None):
    """
    Generates a CSV string with 'count' applicants.
    If 'custom_rows' is provided (list of dicts), these rows are used first.
    If len(custom_rows) < count, the rest are generated randomly.
    If len(custom_rows) > count, all custom rows are used (count is ignored/expanded).
    """
    output = io.StringIO()
    # Header matching `settings.py` expectation: 
    fieldnames = ["id", "jmeno", "prijmeni", "email", "telefon", "datum_narozeni", "bydliste", "skola", "oblast_kultury", "povaha", "intenzita_vyuzivani", "zdroje", "kde", "volne_sdeleni", "barvy", "souhlas"]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    rows_to_write = []
    
    # Add custom rows if any
    if custom_rows:
        for cr in custom_rows:
            # Merge with default structure to ensure all fields exist
            base = generate_applicant()
            base.update(cr)
            rows_to_write.append(base)
            
    # Fill the rest with random data
    remaining = count - len(rows_to_write)
    for _ in range(remaining):
        rows_to_write.append(generate_applicant())
        
    # Write to CSV with IDs
    for i, row in enumerate(rows_to_write):
        row['id'] = i + 1
        writer.writerow(row)
        
    return output.getvalue().encode('utf-8-sig') # UTF-8 with BOM
