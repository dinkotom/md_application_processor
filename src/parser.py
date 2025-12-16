import re
from typing import Dict, Optional
from src.gender_utils import guess_gender
from datetime import datetime

def datetime_cz(value):
    """Format datetime string to Czech format"""
    if not value:
        return ""
    try:
        # Handle microseconds if present (SQLite default)
        if '.' in str(value):
            value = str(value).split('.')[0]
            
        # Value comes from SQLite as YYYY-MM-DD HH:MM:SS
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d. %m. %Y %H:%M:%S')
    except (ValueError, TypeError):
        return value

def datetime_cz_minutes(value):
    """Format datetime string to Czech format (minutes only)"""
    if not value:
        return ""
    try:
        # Handle microseconds if present
        if '.' in str(value):
            value = str(value).split('.')[0]
            
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d. %m. %Y %H:%M')
    except (ValueError, TypeError):
        return value

def slugify_status(status):
    """Convert status to CSS class friendly slug"""
    if not status:
        return 'nova'
    
    s = status.lower()
    replacements = {
        'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e',
        'í': 'i', 'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's',
        'ť': 't', 'ú': 'u', 'ů': 'u', 'ý': 'y', 'ž': 'z',
        ' ': '-'
    }
    
    for old, new in replacements.items():
        s = s.replace(old, new)
        
    return s

def normalize_phone(phone):
    """Basic phone normalization"""
    if not phone:
        return phone
    # Remove whitespace
    return phone.replace(' ', '')

def normalize_school(school_name):
    """Normalize school names to group similar variations"""
    if not school_name:
        return school_name
    
    school = school_name.strip()
    school_lower = school.lower()
    
    # Define normalization rules
    normalizations = [
        (['ostravská univerzita', 'osu'], 'Ostravská univerzita'),
        (['všb-tuo', 'všb'], 'VŠB-TUO'),
    ]
    
    for variations, canonical in normalizations:
        for variation in variations:
            if variation in school_lower:
                return canonical
    return school

def calculate_age(dob_str):
    """Calculate age from DOB string (DD.MM.YYYY or DD/MM/YYYY)"""
    try:
        if not dob_str:
            return None
        clean_dob = dob_str.strip().replace('/', '.')
        dob = datetime.strptime(clean_dob, '%d.%m.%Y')
        today = datetime.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if age <= 0:
            return None
        return age
    except (ValueError, TypeError):
        return None

def parse_email_body(body: str) -> Dict[str, str]:
    """
    Parses the email body to extract application details.
    
    Args:
        body: The raw text content of the email.
        
    Returns:
        A dictionary containing specific fields (first_name, last_name, etc.)
        and a 'full_text' field with the original Q&A.
    """
    data = {}
    
    # Normalize line endings
    lines = body.strip().splitlines()
    
    # Extract Membership ID (usually the last non-empty line)
    membership_id = None
    for line in reversed(lines):
        if line.strip().isdigit():
            membership_id = line.strip()
            break
    data['membership_id'] = membership_id

    # Regex patterns for specific fields
    # Using [ \t]* after colon to match spaces/tabs but NOT newlines
    # Using [^\n]* to match until end of line (including empty values)
    patterns = {
        'first_name': r'Jak se jmenuješ\?\s*:[ \t]*([^\n]*)',
        'last_name': r'Jaké je tvé příjmení\?\s*:[ \t]*([^\n]*)',
        'email': r'Kam ti můžeme poslat e-mail\?[^\n]*:[ \t]*([^\n]*)',
        'phone': r'Na jaké číslo ti můžeme zavolat\?\s*:[ \t]*([^\n]*)',
        'dob': r'Kdy ses narodil(?:/a)?\?\s*:[ \t]*([^\n]*)',
        'city': r'Odkud pocházíš\?\s*:[ \t]*([^\n]*)',
        'school': r'Kam chodíš do školy\?\s*:[ \t]*([^\n]*)',
        'interests': r'Co tě nejvíc zajímá\?\s*:[ \t]*([^\n]*)',
        'character': r'Jsi\s*\.\.\.\s*:[ \t]*([^\n]*)',
        'frequency': r'Jak často během roku chceš navštěvovat doprovodný program Mladého diváka\?\s*:[ \t]*([^\n]*)',
        'source': r'Odkud ses o nás dozvěděl(?:/a)?\?\s*:[ \t]*([^\n]*)',
        'source_detail': r'(?:Odkud\?|Jinde\?)\s*:[ \t]*([^\n]*)',
        'message': r'Chceš nám něco říct\?\s*:[ \t]*([^\n]*)',
        'color': r'Zelená nebo růžová\?\s*:[ \t]*([^\n]*)',
        'newsletter': r'Nesouhlas se zasíláním novinek\s*:[ \t]*([^\n]*)',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
        else:
            data[key] = ""

    # Convert newsletter to Boolean
    # If "Nesouhlas se zasíláním novinek:" is empty, newsletter is TRUE
    # If it contains text, newsletter is FALSE
    newsletter_text = data.get('newsletter', '').strip()
    data['newsletter'] = 1 if not newsletter_text else 0

    # Guess Gender
    data['guessed_gender'] = guess_gender(data.get('first_name', ''), data.get('last_name', ''))
    
    # Store the full body for the document
    data['full_body'] = body
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Parsed email: Name='{data.get('first_name')}' '{data.get('last_name')}', Gender='{data.get('guessed_gender')}'")
    
    return data

def parse_csv_row(row: Dict[str, str]) -> Dict[str, str]:
    """
    Parses a CSV row dictionary into the application data format.
    
    Args:
        row: A dictionary representing a row from the CSV file.
        
    Returns:
        A dictionary containing mapped fields.
    """
    # Get newsletter value and convert to Boolean
    # If field is empty, newsletter is TRUE (1)
    # If it contains text (disagreement), newsletter is FALSE (0)
    # Check multiple possible header names
    newsletter_text = (
        row.get('marketingovy_nesouhlas') or 
        row.get('marketingový nesouhlas') or 
        row.get('Marketingový nesouhlas') or 
        row.get('souhlas') or 
        ''
    ).strip()
    
    if newsletter_text.lower() == 'ano':
        newsletter_value = 1
    else:
        newsletter_value = 1 if not newsletter_text else 0
    
    return {
        'first_name': row.get('jmeno', '').strip(),
        'last_name': row.get('prijmeni', '').strip(),
        'email': row.get('email', '').strip(),
        'phone': row.get('telefon', '').strip(),
        'dob': row.get('datum_narozeni', '').strip(),
        'membership_id': (
            row.get('id') or 
            row.get('ID') or 
            row.get('cislo_karty') or 
            row.get('číslo_karty') or 
            row.get('cislo karty') or
            row.get('číslo karty') or
            row.get('membership_id') or 
            row.get('card_number') or 
            ''
        ).strip(),
        'city': row.get('bydliste', '').strip(),
        'school': row.get('skola', '').strip(),
        'interests': row.get('oblast_kultury', '').strip(),
        'character': row.get('povaha', '').strip(),
        'frequency': row.get('intenzita_vyuzivani', '').strip(),
        'source': row.get('zdroje', '').strip(),
        'source_detail': row.get('kde', '').strip(),
        'message': row.get('volne_sdeleni', '').strip(),
        'color': row.get('barvy', '').strip(),
        'newsletter': newsletter_value,
        'guessed_gender': guess_gender(row.get('jmeno', '').strip(), row.get('prijmeni', '').strip()),
        'full_body': ''  # CSV imports don't have email body
    }

if __name__ == "__main__":
    # Test with the sample provided
    sample_body = """
Jak se jmenuješ?: Barbora
Jaké je tvé příjmení?: Smékalová
Kam ti můžeme poslat e-mail? (lepší osobní než studentský): barus.smekalova@outlook.cz
Na jaké číslo ti můžeme zavolat?: +420777603960
Kdy ses narodil?: 14/05/2000
Odkud pocházíš?: Ostrava
Kam chodíš do školy? : OSU
Co tě nejvíc zajímá? : Divadlo, Hudba
Jsi ...: Něco mezi
Jak často během roku chceš navštěvovat doprovodný program Mladého diváka?: 3
Odkud ses o nás dozvěděl?: Ve škole
Odkud?:
Chceš nám něco říct?:
Zelená nebo růžová?: Zelená
Nesouhlas se zasíláním novinek: Nesouhlasím se zasíláním novinek formou newsletteru a informací o akcích, které probíhají v rámci klubu Mladého diváka.

1954
    """
    parsed = parse_email_body(sample_body)
    print(parsed)
