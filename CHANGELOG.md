## [1.4] - 2025-11-29

### Přidáno
- **Integrace Ecomail API**: Plná integrace s Ecomail pro správu kontaktů
  - Export uchazečů do Ecomail s automatickým vytvořením/aktualizací odběratelů
  - Vyhledávání odběratelů podle emailové adresy v sekci Pokročilé
  - Automatická detekce a výběr kontaktního seznamu (preferuje seznam "TEST")
  - Podpora standardních polí: email, jméno, příjmení, telefon, město, datum narození
  - Export tagů z zájmů, povahy a barvy
  - Export členského čísla jako vlastního pole (CLENSKE_CISLO)
- **Poznámky k uchazečům**: Možnost přidávat poznámky k jednotlivým uchazečům
  - Automatické ukládání poznámek při opuštění textového pole
  - Indikátory stavu ukládání (Ukládání..., ✓ Uloženo, ✗ Chyba)
  - Podpora poznámek ze seznamu i detailní stránky
- **Vlastní modální okna**: Nahrazení nativních dialogů vlastními modály
  - Potvrzení exportu do Ecomailu
  - Úspěšný export do Ecomailu
  - Konzistentní design napříč aplikací

### Změněno
- **UI detailní stránky**: Vylepšené rozložení tlačítek
  - Menší tlačítka (btn-small) pro kompaktnější vzhled
  - Vizuální oddělení navigačních tlačítek od akčních tlačítek
  - Zjednodušená navigace: "←" a "→" místo "Předchozí" a "Následující"
  - Responzivní layout s horizontálním oddělovačem na mobilních zařízeních
- **Ecomail export**: Optimalizovaná struktura dat
  - Konverze data narození z DD/MM/YYYY na YYYY-MM-DD formát
  - Tagy na nejvyšší úrovni API požadavku (mimo subscriber_data)
  - Odstranění nadbytečných vlastních polí (ponecháno pouze CLENSKE_CISLO)
  - Město jako standardní pole místo vlastního pole

### Opraveno
- **Ecomail export**: Opravena chyba 404 při exportu uchazečů
  - Přidána chybějící route `/applicant/<id>/export_to_ecomail`
  - Implementována metoda `create_subscriber` v EcomailClient
- **Vyhledávání odběratelů**: Přidána chybějící route `/ecomail/subscriber`
- **Export města**: Opraveno odesílání pole město do Ecomailu
- **Export data narození**: Správná konverze formátu data pro Ecomail API
- **Export tagů**: Tagy nyní správně exportovány na nejvyšší úrovni požadavku

### Technické
- Nový modul: `src/ecomail.py` s třídou `EcomailClient`
  - Metody: `get_lists()`, `get_subscriber()`, `create_subscriber()`
  - Podpora pro vytváření a správu kontaktních seznamů
- Nové routy:
  - `POST /applicant/<id>/export_to_ecomail` - export uchazeče do Ecomailu
  - `POST /ecomail/subscriber` - vyhledávání odběratele
  - `POST /applicant/<id>/update_note` - aktualizace poznámky
- Databázové změny:
  - Přidán sloupec `note` (TEXT) do tabulky applicants
  - Přidán sloupec `exported_to_ecomail` (INTEGER) do tabulky applicants
  - Přidán sloupec `exported_at` (TIMESTAMP) do tabulky applicants
- Vylepšené logování pro ladění Ecomail exportu

---

## [1.2] - 2025-11-28

### Přidáno
- **Inline úpravy**: Úprava údajů uchazeče přímo na detailní stránce pomocí ikon tužky
  - Editovatelná pole: Jméno, Příjmení, Email, Telefon, Datum narození, Stav
  - Datum narození s výběrem kalendáře (HTML5 date picker)
  - AJAX endpoint `/applicant/<id>/update_field` pro okamžité aktualizace
- **Navigace mezi uchazeči**: Tlačítka "Předchozí" a "Následující" na detailní stránce
  - Respektuje aktuální filtry a řazení
  - Zachování kontextu při procházení seznamu
- **Perzistence stránkování**: Tlačítko "Zpět na seznam" vrací na správnou stránku seznamu
- **Upozornění na věk**: Přesunuté do oblasti upozornění v horní části detailní stránky
- Testy pro inline úpravy polí (`test_update_applicant_field`, `test_update_applicant_field_invalid`, `test_update_applicant_dob`)

### Změněno
- **UI detailní stránky**: Seskupení navigačních tlačítek odděleně od akčních tlačítek
- **Modální okno úprav**: Odstraněno ve prospěch inline úprav
- Vrácena původní velikost členské karty (1024x585) pro lepší kvalitu
- Vylepšená kvalita QR kódu pomocí `Image.LANCZOS` filtru
- Optimalizace PNG výstupu členské karty (`optimize=True`)

### Opraveno
- Opravena chyba `sqlite3.ProgrammingError` při aktualizaci údajů uchazeče (duplicitní `conn.close()`)
- Opravena chyba `NameError: name 'conn' is not defined` v index route
- Opravena chyba `AssertionError: View function mapping is overwriting an existing endpoint function`
- Přidán chybějící `{% block scripts %}` do `base.html` pro načítání JavaScriptu

### Technické
- Nový endpoint: `POST /applicant/<id>/update_field` pro AJAX aktualizace jednotlivých polí
- Refaktoring: Extrahována funkce `get_filtered_applicants()` pro znovupoužitelnost
- Konverze formátu data: DD.MM.YYYY ↔ YYYY-MM-DD pro HTML5 date picker
- Rozšířené testy v `tests/test_web_app.py`

---

## [1.1] - 2025-11-27

### Přidáno
- **Funkce odesílání emailů**: Odesílání členských karet emailem s náhledem a potvrzením
- Editor šablony emailu v sekci Pokročilé s podporou zástupných symbolů
- Sledování emailů (stav odeslání a časová značka) v databázi
- Bezpečnost TEST režimu: všechny emaily v testovacím režimu jdou na nakonfigurovanou testovací adresu
- Modální okno náhledu emailu zobrazující příjemce, předmět, text a přílohy
- Česká lokalizace všech funkcí souvisejících s emailem
- Soubor historie změn a zobrazení na stránce Pokročilé

### Změněno
- Aktualizováno číslo verze z 1.0 na 1.1
- Vylepšeno rozložení tabulky: odstraněn sloupec telefonního čísla, zmenšena velikost písma
- Opraven problém se zalamováním data přijetí přihlášky
- Opraveno přetékání emailové adresy na detailní stránce
- Změněno rozložení detailní stránky z 1x4 na 2x2 dlaždice
- **Zmenšena velikost písma na členské kartě** z 45 na 25 bodů pro lepší umístění dlouhých jmen
- **Upravena pozice členského čísla** na kartě (posunuto o 8 pixelů níže)
- **Změněna konvence pojmenování souborů** členských karet na formát `id_jmeno_prijmeni.png` (bez diakritiky)
- **Změněna adresa odesílatele** na `info@mladydivak.cz` (From a Reply-To)
- **Přidána favicona** (logo md)
- Přeložena historie změn do češtiny
- Odstraněna redundantní hlavička z historie změn

### Technické
- Přidána databázová tabulka `email_template`
- Přidány sloupce `email_sent` a `email_sent_at` do tabulky applicants
- Vytvořen modul `src/email_sender.py` pro emailovou funkcionalitu
- Přidány emailové routy: `/email/template`, `/applicant/<id>/email/preview`, `/applicant/<id>/email/send`
- Přidána route `/changelog` pro zobrazení historie změn
- **Logování aplikace**: Implementováno logování do souboru `app.log` (vyloučeno z git) pro sledování akcí a chyb

---

## [1.0] - 2025-11-27

### Přidáno
- Počáteční vydání
- Webový dashboard pro prohlížení a správu uchazečů
- Stahování emailů z Gmailu
- Generování členských karet s QR kódy
- Stránka statistik s filtrováním
- Funkce importu/exportu CSV
- Podpora duálního režimu (testovací/produkční databáze)
- Sledování a řazení podle data přijetí přihlášky
- Filtrování a varování podle věku
- Normalizace škol a měst
- Detekce duplicit
- Správa stavů (Nová, Zpracovává se, Vyřízená)

### Funkce
- Seznam uchazečů s stránkováním
- Detailní zobrazení uchazeče
- Možnosti vyhledávání a filtrování
- Náhled a stažení členské karty
- Přepínání režimů (Test/Produkce)
- Nástroje pro správu databáze
