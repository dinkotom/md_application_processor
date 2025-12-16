from src.parser import parse_email_body
from src.gender_utils import guess_gender

sample_body = """
Jak se jmenuješ?: Barbora
Jaké je tvé příjmení?: Smékalová
Kam ti můžeme poslat e-mail? (lepší osobní než studentský): barus.smekalova@outlook.cz
"""

sample_body_empty = """
Jak se jmenuješ?: 
Jaké je tvé příjmení?: 
"""

sample_body_weird_spacing = """
Jak se jmenuješ?   :   Jan   
Jaké je tvé příjmení? :   Novák   
"""

print(f"--- Standard Sample ---")
parsed = parse_email_body(sample_body)
print(f"Name: {parsed['first_name']} {parsed['last_name']}")
print(f"Gender: {parsed['guessed_gender']}")

print(f"\n--- Empty Sample ---")
parsed = parse_email_body(sample_body_empty)
print(f"Name: '{parsed['first_name']}' '{parsed['last_name']}'")
print(f"Gender: {parsed['guessed_gender']}")

print(f"\n--- Weird Spacing Sample ---")
parsed = parse_email_body(sample_body_weird_spacing)
print(f"Name: '{parsed['first_name']}' '{parsed['last_name']}'")
print(f"Gender: {parsed['guessed_gender']}")

print(f"\n--- Direct Guess Check ---")
print(f"Jana: {guess_gender('Jana', '')}")
print(f"Petr: {guess_gender('Petr', '')}")
print(f"Jan: {guess_gender('Jan', '')}")
print(f"Empty: {guess_gender('', '')}")
