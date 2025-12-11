
import re

def guess_gender(first_name: str, last_name: str) -> str:
    """
    Guess gender based on Czech naming conventions.
    Returns: 'male', 'female', or 'unknown'
    """
    if not first_name:
        return 'unknown'
    
    first_name = first_name.strip()
    last_name = last_name.strip() if last_name else ""
    
    # Normalize for easier checking
    fn_lower = first_name.lower()
    ln_lower = last_name.lower()
    
    # 1. Check Surname (Strongest signal in Czech)
    # Most female surnames end in 'á'
    if ln_lower.endswith('á'):
        return 'female'
        
    # 2. Check First Name
    # Male exceptions ending in 'a'
    male_exceptions_a = {
        'honza', 'pepa', 'láďa', 'míra', 'jirka', 'tom', 'mustafa', 'nikola', 'luca', 'sasha', 'břeťa', 'viťa'
    }
    
    # Female exceptions not ending in 'a' or 'e'/'ie'
    female_exceptions_other = {
        'nela', 'dagmar', 'miriam', 'ester', 'ruth', 'rachel', 'karen', 'carmen', 'zoe' 
    }

    # If first name ends in 'a'
    if fn_lower.endswith('a'):
         if fn_lower in male_exceptions_a:
             return 'male'
         return 'female'

    # If first name ends in 'ie' (e.g., Lucie, Marie, Sofie)
    if fn_lower.endswith('ie'):
        return 'female'
        
    # If first name ends in 'e' (could be female like Libuše, or male like Mike)
    # Common female names ending in 'e' but not 'ie'
    if fn_lower.endswith('e') and not fn_lower.endswith('ie'):
         # Check known males ending in e
         if fn_lower in ['mike', 'dave', 'steve', 'joe', 'dan', 'kae']: 
             return 'male'
         # Default assumption for 'e' in Czech context often female (Libuše, Danuše)
         # But 'George' is male. It's tricky.
         # Let's list common Czech female names ending in 'e'
         if fn_lower in ['libuše', 'danuše', 'miluše', 'květuše', 'dagmar', 'alice', 'beatrice', 'charlotte', 'denise', 'eliane', 'emilie', 'eveline', 'justine', 'michelle', 'nicole', 'noemi', 'simone', 'sylvie', 'vivien', 'zoe']:
             return 'female'
         
    # Check if in known female list (non-standard endings)
    if fn_lower in female_exceptions_other:
        return 'female'

    # Default to Male
    return 'male'
