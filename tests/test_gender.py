
import unittest
from src.gender_utils import guess_gender

class TestGenderUtils(unittest.TestCase):
    def test_females(self):
        names = [
            ("Jana", "Nováková"),
            ("Marie", "Svobodová"),
            ("Lucie", "Kovářová"),
            ("Eva", "Procházková"),
            ("Barbora", "Smékalová"), # From example
            ("Alice", "Dvořáková"),
            ("Dagmar", "Havlová"),
            ("Adéla", "Nová"),
            ("Sofie", "Malá")
        ]
        for fn, ln in names:
            with self.subTest(name=f"{fn} {ln}"):
                self.assertEqual(guess_gender(fn, ln), 'female')

    def test_males(self):
        names = [
            ("Jan", "Novák"),
            ("Petr", "Svoboda"),
            ("Tomáš", "Kovář"),
            ("Jiří", "Procházka"),
            ("Pavel", "Dvořák"),
            ("Honza", "Novotný"), # Exception ending in a
            ("Jakub", "Maly"),
            ("Martin", "Veselý"),
            ("David", "Kříž")
        ]
        for fn, ln in names:
            with self.subTest(name=f"{fn} {ln}"):
                self.assertEqual(guess_gender(fn, ln), 'male')

    def test_ambiguous_or_complex(self):
        # Taking reasonable guesses
        self.assertEqual(guess_gender("Nikola", "Tesla"), 'male') # 'Nikola' can be male or female, but surname doesn't end in 'á' -> likely male in Czech context if international usage, or ambiguous. 
        # Actually Nikola is often female in CZ today, but classically male in Balkan.
        # My logic: surname Tesla (no 'á') -> skips female check -> Nikola ends in 'a' -> is it in exceptions? Yes I put it there. -> male.
        # Wait, Nikola IS common female name in CZ. But surname suggests non-female form?
        # If the user is "Nikola Nováková", surname check catches it as female.
        # If "Nikola Novák", likely male.
        # So my priority (Surname -> Firstname) works well.
        
        self.assertEqual(guess_gender("Nikola", "Nováková"), 'female')

if __name__ == '__main__':
    unittest.main()
