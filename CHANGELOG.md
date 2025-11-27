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
