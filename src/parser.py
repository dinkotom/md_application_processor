import re
from typing import Dict, Optional

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
        'character': r'Jsi\\s*\\.\\.\\.\\s*:[ \t]*([^\\n]*)',
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

    # Store the full body for the document
    data['full_body'] = body
    
    return data

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
