## [1.8.4] - 2026-01-11

### Přidáno
- **Export**: Přidána možnost filtrování exportu podle stavu přihlášky (multi-select) s možností uložení do předvoleb.
- **UI**: Duplikována paginace i nad seznam přihlášek pro lepší navigaci. Horní paginace je umístěna v liště filtrů.
- **UI**: Paginace zůstává viditelná (deaktivovaná) i při jedné stránce výsledků, aby se zabránilo poskocích layoutu.

### Změněno
- **Hledání**: Vyhledávání je nyní ignoruje diakritiku (např. "Štěpán" najde i "Stepan").
- **Export**: Přejmenováno pole "Status" na "Stav" pro sjednocení názvosloví.

### Opraveno
- **Navigace**: Opraveno přesměrování po změně stavu nebo smazání přihlášky - aplikace nyní zachovává aktuální stránku, filtry a řazení.
- **Ecomail**: Opravena chyba 422 při synchronizaci kontaktů obsahujících čárky ve štítcích (např. v poli charakter nebo škola).

---

## [1.8.3] - 2025-12-14

### Opraveno
- **Deployment**: Opraveno načítání šablony uvítacího emailu na produkčním serveru (PythonAnywhere). Implementováno robustnější vyhledávání cesty k souboru šablony.
- **Diagnostika**: Přidáno zobrazení cesty k souboru šablony v případě chyby načítání na stránce Pokročilé.

---

## [1.8.2] - 2025-12-14

### Přidáno
- **Náhled uvítacího emailu**: Přidána sekce na stránku "Pokročilé" (Advanced), která zobrazuje aktuální podobu uvítacího emailu, který je odesílán uchazečům. Slouží pro rychlou kontrolu vzhledu šablony.

---

## [1.8.1] - 2025-12-14

### Opraveno
- **Duplicitní stahování**: Opravena chyba v UI, kdy bylo možné dvojklikem na potvrzovací tlačítko spustit proces stahování/importu (Email i CSV) dvakrát, což vedlo k duplicitním datům. Tlačítka se nyní po kliknutí okamžitě deaktivují.

---

## [1.8.0] - 2025-12-12

### Přidáno
- **Export do Excelu s Drag & Drop**:
  - Nový moderní interface pro export přihlášek.
  - Možnost výběru specifických polí pro export.
  - **Drag & Drop řazení**: Uživatel si může určit pořadí sloupců v Excelu přetažením položek.
  - Překlad hodnot (např. pohlaví: male -> muž, female -> žena).

### Odebráno
- **Legacy Exporty**: Odstraněn zastaralý export do CSV a hromadný export do Ecomailu z rozhraní i backendu.

### Instalace pro tento release
> [!IMPORTANT]
> Pro správnou funkci exportů je nutné nainstalovat nové závislosti (ujistěte se, že máte aktivní virtuální prostředí):
> ```bash
> source venv/bin/activate
> pip install -r requirements.txt
> ```

---

## [1.7.4] - 2025-12-11

### Přidáno
- **Editace pohlaví**: Možnost ručně upravit odhadované pohlaví přímo na detailu uchazeče.
- **Třetí možnost pohlaví**: Přidána možnost "Neuvedeno" pro případy, kdy pohlaví není známé nebo jej nelze určit.

### Změněno
- **Bezpečnější migrace**: Skript pro detekci pohlaví (migrace) nyní respektuje již existující hodnoty a nepřepisuje manuální změny.

---

## [1.7.3] - 2025-12-11

### Přidáno
- **Klikatelné statistiky pohlaví**: Možnost filtrovat seznam uchazečů kliknutím na statistiky pohlaví (Muži, Ženy) na stránce statistik.
- **Vylepšená instalace**: Aktualizovaný skript `migrate_all.py` nyní zahrnuje i migraci pro detekci pohlaví, což zjednodušuje setup aplikace.

### Změněno
- **Backend Statistik**: Logika statistik již nezobrazuje kategorii "Neznámé", pokud nejsou žádní uchazeči s neznámým pohlavím (výchozí stav je "Muž").

---

## [1.7.2] - 2025-12-09

### Změněno
- **Uvítací email**: Odstranění zbytečných mezer (paddingů) kolem obrázku a nad/pod sekcí "Vybrané tituly" na mobilu.

---

## [1.7.1] - 2025-12-09

### Změněno
- **Uvítací email**: Snížení vertikálních mezer u sekce "Vybrané tituly" na mobilních zařízeních (úprava paddingu).

---

## [1.7] - 2025-12-09

### Změněno
- **Uvítací email**: Optimalizace zobrazení na mobilních zařízeních
  - Zvětšení písma v sekci "Vybrané tituly" (Nadpis: 20px, Text: 16px) pro lepší čitelnost
  - Zarovnání textu na střed na malých obrazovkách
  - Implementace pomocí **inline stylů** pro zajištění správného zobrazení ve všech emailových klientech

---

## [1.6] - 2025-12-06

### Přidáno
- **Filtrování podle povahy**: Přidány statistiky povahy na stránku statistik
  - Kliknutím na číslo u povahy dojde k vyfiltrování seznamu uchazečů
  - Statistiky seřazeny sestupně podle počtu a abecedně
- **Vylepšené stránkování**:
  - Přidána tlačítka pro první (`<<`) a poslední (`>>`) stránku
  - Přidán seznam čísel stránek s indikací aktuální stránky a inteligentním zkracováním (`1 ... 4 5 6 ... 10`)
  - Vylepšený design stránkování v ladícím stylu aplikace
- **Konzistentní design**: Sjednocení stylu tlačítek a odkazů v tabulkách

### Změněno
- **Web App**:
  - `stats` route nyní počítá a předává statistiky povahy
  - `get_filtered_applicants` podporuje filtrování podle `character`
  - `index` route zachovává `page` a filtry v URL pro lepší UX při navigaci
- **UI**:
  - Aktualizována šablona `stats.html` pro zobrazení sekce "Povaha"
  - Aktualizována šablona `index.html` pro nové stránkovací komponenty
  - Aktualizován `style.css` pro styly stránkování

### Technické
- Přidán test `test_filter_by_character` pro ověření filtrování
- Přidán test `test_pagination` pro ověření generování odkazů na stránky

### Migrace
> [!IMPORTANT]
> Pro nasazení této verze na existující instalaci je doporučeno spustit migrační skript pro vyčištění databáze:
> ```bash
> python3 migrate_remove_email_template.py
> ```

---

## [1.5] - 2025-12-05

### Přidáno
- **Auditní stopa (Audit Trail)**: Kompletní historie změn u uchazečů
  - Sledování změn v polích (jméno, stav, poznámky, atd.)
  - Záznam odeslání uvítacích emailů a exportů do Ecomailu
  - Změny zobrazeny v přehledné tabulce "Historie aktivit" na detailní stránce uchazeče
  - Lokalizované datum a čas (český formát)
  - Záznam původní a nové hodnoty pro každou změnu

### Změněno
- **UI Tabulky historie**: Vylepšený design pro lepší čitelnost
  - Oddělení sloupců svislými čarami
  - Zvýrazněné záhlaví a pruhované řádky
  - Zvětšené odsazení pro pohodlnější čtení
  - Responzivní zobrazení
- **Formátování data**: Datum v historii aktivit je nyní ve formátu `d. m. YYYY HH:MM:SS`
- **Konfigurace testů**: Opravena inicializace databáze v testech (`init_db` nyní vytváří tabulku `audit_logs`)

### Technické
- Nová databázová tabulka `audit_logs`
- Pomocná funkce `log_action` pro centralizované logování
- Vlastní Jinja2 filtr `datetime_cz` pro formátování data
- Rozšíření testů v `test_web_app.py` o vytváření auditní tabulky

---

## [1.4] - 2025-12-03

### Změněno
- **UI Navigace**: Kompletní refaktoring navigační lišty
  - Oddělení přihlašovacích prvků od hlavní navigace
  - Přesun uživatelského jména a tlačítka odhlášení doprava
  - Zmenšení písma uživatelského jména a jeho umístění pod tlačítko odhlášení
  - Responzivní chování pro menší obrazovky
- **OAuth Konfigurace**: Povolení `OAUTHLIB_INSECURE_TRANSPORT` pro vývojové prostředí (localhost)
  - Oprava chyby `MismatchingStateError` při přihlašování
  - Úprava nastavení session cookies (SameSite=Lax)

---

## [1.3] - 2025-11-29

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
- **Newsletter Logic:**
    - Converted `newsletter` field to Boolean (INTEGER 0/1) in database.
    - Updated parsers (Email & CSV) to correctly interpret consent:
        - Email: Checks `Nesouhlas se zasíláním novinek` (Empty = 1, Text = 0).
        - CSV: Checks `marketingovy_nesouhlas` (Empty = 1, Text = 0).
    - Updated Ecomail integration to respect subscription status:
        - New subscribers: `status=1` (Subscribed) if newsletter=1, `status=2` (Unsubscribed) if newsletter=0.
        - Existing subscribers: Status is preserved (`resubscribe=False`).
    - UI now displays "Ano"/"Ne" for newsletter consent.
- **Database:**
    - Added migration `migrate_newsletter_integer.py` to convert legacy text data to integer.
    - Updated schema to enforce `INTEGER NOT NULL DEFAULT 1` for newsletter.
- **Deployment:**
    - Added `requests` to `requirements.txt`.
    - Updated `start_app.sh` and `start_app.command` to automatically install dependencies on startup.

### Opraveno
- **Ecomail export**: Opravena chyba 404 při exportu
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
