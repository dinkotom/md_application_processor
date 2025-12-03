import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import parse_email_body, parse_csv_row

class TestParser(unittest.TestCase):
    
    def test_parse_email_body(self):
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
        data = parse_email_body(sample_body)
        
        self.assertEqual(data['first_name'], 'Barbora')
        self.assertEqual(data['last_name'], 'Smékalová')
        self.assertEqual(data['email'], 'barus.smekalova@outlook.cz')
        self.assertEqual(data['phone'], '+420777603960')
        self.assertEqual(data['dob'], '14/05/2000')
        self.assertEqual(data['city'], 'Ostrava')
        self.assertEqual(data['school'], 'OSU')
        self.assertEqual(data['interests'], 'Divadlo, Hudba')
        self.assertEqual(data['character'], 'Něco mezi')
        self.assertEqual(data['frequency'], '3')
        self.assertEqual(data['source'], 'Ve škole')
        self.assertEqual(data['color'], 'Zelená')
        self.assertEqual(data['membership_id'], '1954')
        self.assertEqual(data['newsletter'], 0)

    def test_parse_csv_row(self):
        row = {
            'jmeno': 'Jan',
            'prijmeni': 'Novák',
            'email': 'jan.novak@example.com',
            'telefon': '123456789',
            'datum_narozeni': '01.01.2000',
            'id': '9999',
            'bydliste': 'Praha',
            'skola': 'VŠE',
            'oblast_kultury': 'Film',
            'povaha': 'Introvert',
            'intenzita_vyuzivani': '5',
            'zdroje': 'Internet',
            'kde': 'Facebook',
            'volne_sdeleni': 'Ahoj',
            'barvy': 'Modrá',
            'souhlas': 'Ano'
        }
        
        data = parse_csv_row(row)
        
        self.assertEqual(data['first_name'], 'Jan')
        self.assertEqual(data['last_name'], 'Novák')
        self.assertEqual(data['email'], 'jan.novak@example.com')
        self.assertEqual(data['phone'], '123456789')
        self.assertEqual(data['dob'], '01.01.2000')
        self.assertEqual(data['membership_id'], '9999')
        self.assertEqual(data['city'], 'Praha')
        self.assertEqual(data['school'], 'VŠE')
        self.assertEqual(data['interests'], 'Film')
        self.assertEqual(data['character'], 'Introvert')
        self.assertEqual(data['frequency'], '5')
        self.assertEqual(data['source'], 'Internet')
        self.assertEqual(data['source_detail'], 'Facebook')
        self.assertEqual(data['message'], 'Ahoj')
        self.assertEqual(data['color'], 'Modrá')
        self.assertEqual(data['newsletter'], 1)
        self.assertEqual(data['full_body'], '')

if __name__ == '__main__':
    unittest.main()
