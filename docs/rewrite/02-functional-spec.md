# 02 – Funkční specifikace nové aplikace COBOL AIRLINES

Specifikace je odvozena z legacy kódu popsaného v `01-inventory.md`. Každý use case a obrazovka uvádí **zdroj** (legacy program/mapa) a označuje, co je **rekonstrukce** (chování existuje v originálu) a co je **návrh** (v originálu chybí, doplněno tak, aby role měly smysluplnou náplň). Kde specifikace záměrně mění chování originálu, je to označeno **Odchylka**.

Podle tohoto dokumentu se píše nová aplikace. Pořadí implementace určuje `04-migration-plan.md`.

## 0. Konvence

- **Jazyk UI:** angličtina (jako originál). Texty hlášek jsou převzaty z legacy tam, kde existují, s opravou překlepů (např. „AVAIBLE“ → „available“). Dokumentace je česky.
- **Názvy entit a polí** v této specifikaci jsou původní názvy DB2 (`FLIGHTNUM`, `CLIENTID`, …). V kódu aplikace se používají malá písmena (`flightnum`, `clientid`) – viz `03-target-architecture.md`.
- **Datum:** vstup i výstup `YYYY-MM-DD` (ISO, jako legacy vstupy). Hlavička obrazovky zobrazuje datum a čas v zóně `Europe/Paris`.
- **Čas:** `HH:MM`.
- **Měna:** EUR, dvě desetinná místa, formát `120.99 EUR`. (**Odchylka:** legacy obrazovka zobrazovala `$`.)
- **Identifikátory:**
  - `EMPID` – 8 číslic jako text (`10000006`), přihlašovací jméno.
  - `CLIENTID` – celé číslo (identity).
  - `FLIGHTNUM` – `CB` + 4 číslice; `FLIGHTID` je interní a v UI se nezobrazuje (v URL ano).
  - `TICKETID` – `CB` + 8 číslic, generováno ze sekvence (`CB00000001`).
  - `SEAT` – písmeno `A`–`F` + dvě číslice řady (`B04`).
  - `BUYID` – celé číslo (identity), zobrazeno na účtence.
- **Hlášky:** každá obrazovka má oblast pro hlášky (ekvivalent `MSG1`/`MSG2`): chyba (červeně), informace (zeleně). Chybová hláška DB / neočekávaná chyba: „Communication error between system and DB, call IT dept. Error: {kód}“ (legacy text).
- **Limity délek** vstupních polí jsou převzaty z map (uvedeny u každé obrazovky). Delší vstup je chyba validace, ne tiché oříznutí (**Odchylka**: CICS mapy ořezávaly).

## 1. Aktéři a role

Role je odvozena z `EMPLO.DEPTID`. Jeden uživatel = jeden zaměstnanec = jedna role.

| Role (kód) | `DEPTID` | Popis | Rozsah v originálu |
|---|---|---|---|
| `sales` | 7 | Prodejce letenek | Jediná implementovaná role |
| `it` | 6 | IT podpora – správa uživatelů a číselníků | Jen hláška „not available“ |
| `hr` | 5 | Personalistika – zaměstnanci, oddělení | dtto |
| `schedule` | 9 | Plánování – lety, posádky, směny | dtto |
| `crew` | 2, 3, 4 | Letová posádka (velitel, druhý pilot, palubní průvodčí) – čtení vlastních směn | dtto |
| `ceo` | 1 | Vedení – přehledy | dtto |
| `legal` | 8 | Právní – v originálu jen hláška; v cíli pouze přihlášení a domovská stránka | dtto |

### 1.1 Matice oprávnění

| Funkce | sales | it | hr | schedule | crew | ceo | legal |
|---|---|---|---|---|---|---|---|
| Přihlášení, odhlášení, změna vlastního hesla | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Hledání letů | ✓ | – | – | ✓ (čtení) | ✓ (čtení) | ✓ (čtení) | – |
| Hledání letenek, detail, tisk palubní vstupenky | ✓ | – | – | – | – | ✓ (čtení) | – |
| Cestující – seznam, detail | ✓ | – | – | – | – | – | – |
| Cestující – založení, editace | ✓ | – | – | – | – | – | – |
| Prodej letenek, účtenka | ✓ | – | – | – | – | – | – |
| Uživatelé – reset hesla, aktivace/deaktivace | – | ✓ | – | – | – | – | – |
| Číselníky letišť a letadel | – | ✓ | – | ✓ | – | – | – |
| Zaměstnanci – CRUD, oddělení, manažeři | – | – | ✓ | – | – | ✓ (čtení) | – |
| Lety – založení, editace, generování na období | – | – | – | ✓ | – | – | – |
| Posádky a směny – CRUD | – | – | – | ✓ | – | – | – |
| Moje směny a lety | – | – | – | – | ✓ | – | – |
| Přehledy (prodeje, obsazenost) | – | – | – | – | – | ✓ | – |

Přístup na stránku bez oprávnění → HTTP 403 se stránkou „You are not allowed to access this function“ a odkazem na domovskou stránku role.

## 2. Společné prvky obrazovek

Rekonstrukce hlavičky CICS map (`USERID`, `TERMINAL`, `DATE`, `TIME`, titulek, funkční klávesy):

- **Hlavička:** logo/titulek „COBOL AIRLINES – Programming at heights“, přihlášený `EMPID` + jméno, role, aktuální datum a čas (`Europe/Paris`). `TERMINAL` se nahrazuje ničím (nemá web ekvivalent).
- **Navigace (ekvivalent řádku 24):** menu podle role. Pro `sales`: *Search flight* (F4), *Search ticket* (F5), *Sell* (F6), *Passengers* (F7), *Logout* (F3). Klávesové zkratky F3–F7 se v prohlížeči **nepoužívají** (kolidují s prohlížečem); odkazy jsou v menu. Volitelně Alt+číslo.
- **Oblast hlášek** pod hlavičkou.
- **Stránkování** seznamů: 10 řádků na stránku (legacy limit), ovládání *Previous* / *Next* / číslo stránky, text `page n/N`.
- **Formuláře:** validace na serveru; chybové hlášky u polí i souhrnně v oblasti hlášek; hodnoty polí po chybě zůstávají vyplněné (**Odchylka:** legacy je mazal).

## 3. Use cases

### 3.1 Společné

#### UC-A01 Přihlášení (rekonstrukce `LOGIN` + `CRYPTVE`, mapa `LOGON`)

- **Aktér:** kdokoli se záznamem v `EMPLO` a aktivním účtem.
- **Vstupy:** `USERID` (8 znaků, povinné), `PASSWORD` (skryté, povinné, bez horního limitu 8; **Odchylka**).
- **Postup:** ověřit dvojici; při úspěchu založit session a přesměrovat na domovskou stránku role (kap. 4.2). Při neúspěchu zobrazit „Password or userid incorrect.“ **bez rozlišení**, zda uživatel existuje (legacy chování, žádoucí i bezpečnostně).
- **Chybové stavy:** neaktivní účet → stejná hláška jako nesprávné heslo; technická chyba → „Communication error in the system, call the IT dept. Error: {kód}“.
- **Pravidla:** heslo je uloženo jako moderní hash (viz architektura). Legacy hashe nelze převzít. Po 10 neúspěšných pokusech za 15 minut dočasně blokovat IP/účet na 15 minut (**návrh**, bezpečnostní minimum).

#### UC-A02 Odhlášení (rekonstrukce F3 → `LOGIN`)

- Ukončí session, zobrazí přihlašovací stránku s informací „You have been logged out.“

#### UC-A03 Změna vlastního hesla (návrh)

- Vstupy: současné heslo, nové heslo 2×. Pravidla: min. 8 znaků. Po změně zůstává uživatel přihlášen.

#### UC-A04 Domovská stránka role (rekonstrukce větvení v `LOGIN` podle `DEPTID`)

- Po přihlášení každá role vidí svou domovskou stránku s menu. Role bez funkcí (`legal`) vidí text „The {role} functions are not available yet.“ (ekvivalent legacy hlášky).

### 3.2 Sales

#### UC-S01 Hledání letů (rekonstrukce `SRCHFLY`, mapa `SRCHPA`)

- **Vstupy:** `FLIGHT NUM` (max. 6), `DATE` (ISO), `DEP AIRPORT` (3–4 znaky), `LAND AIRPORT` (3–4 znaky). Všechna pole nepovinná, ale alespoň jedno vyplněné.
- **Pravidla vyhledávání:**
  1. Nic nevyplněno → hláška „No data inserted, try again.“, žádný dotaz.
  2. Vyplněná pole se kombinují operátorem AND. (**Odchylka:** legacy ignoroval letiště, pokud bylo zadáno číslo letu; nový systém zadaná pole vždy respektuje, výsledek je tedy podmnožinou legacy výsledku.)
  3. `FLIGHT NUM` – přesná shoda, porovnání bez ohledu na velikost písmen (`cb1104` = `CB1104`).
  4. Letiště – přesná shoda kódu, bez ohledu na velikost písmen.
  5. `DATE` nevyplněno → `FLIGHTDATE >= dnes` (legacy: u čísla letu `>= dnes`, u letišť `= dnes`; **Odchylka** sjednoceno na `>= dnes`).
  6. Řazení: `FLIGHTDATE`, `DEPTIME`, `FLIGHTNUM` (legacy bez řazení).
  7. Stránkování po 10.
- **Validace:** datum ve tvaru `YYYY-MM-DD` a platné → jinak „Wrong date format, try to insert date as YYYY-MM-DD“. Letiště: 3–4 znaky.
- **Výstup – tabulka:** `FID` (`FLIGHTNUM`), `TDEP` (`DEPTIME`), `TLAND` (`ARRTIME`), `DEP` (`AIRPORTDEP`), `LAND` (`AIRPORTARR`), `PLACES` (volná místa, viz kap. 5.3), `DATE`. Navíc (**návrh**) sloupec `PRICE` a odkaz *Sell* předvyplňující prodej (číslo letu + datum).
- **Prázdný výsledek:** „No flight matches the inserted information.“ (**Odchylka:** legacy nechal obrazovku prázdnou).

#### UC-S02 Hledání letenek (rekonstrukce `SRCHTKT`, mapa `SRCHTK`)

- **Vstupy:** `TICKET ID` (10), `CLIENT ID` (číslo), `FIRST NAME` (max. 30), `LAST NAME` (max. 30), `FLIGHT NUM` (6; legacy popisek „FLIGHT ID“), `FLIGHT DATE` (ISO).
- **Pravidla vyhledávání (legacy priority zachovány):**
  1. Je-li vyplněno `TICKET ID` → hledá se jen podle něj (ostatní pole ignorována).
  2. Jinak je-li `CLIENT ID` → podle klienta, volitelně zúženo o `FLIGHT NUM` a/nebo `FLIGHT DATE` (**Odchylka:** legacy dovolil jen jedno z nich).
  3. Jinak je-li `FIRST NAME` **i** `LAST NAME` → podle jména, volitelně zúženo o číslo letu a/nebo datum. Shoda jména: celé jméno, bez ohledu na velikost písmen (legacy: přesná shoda velkými písmeny).
  4. Jinak → chyba „A valid research must have at least: ticket id, or client id, or client's first and last name.“ (i když je vyplněn jen `FLIGHT NUM` nebo `FLIGHT DATE`, nebo jen jedno ze jmen).
- **Validace:** `CLIENT ID` celé kladné číslo; datum ISO; `TICKET ID` formát `CB` + 8 číslic (jinak rovnou „No data match with this inserted information.“).
- **Výstup:** seznam letenek (10 na stránku): `TICKET ID`, `FIRST NAME`, `LAST NAME`, `FLIGHT NUM`, `FLIGHT DATE`, `TIME DEP`, `TIME LAND`, `AIRPORT DEP`, `AIRPORT LAND`, `SEAT`. Řazení `FLIGHTDATE`, `DEPTIME`, `TICKETID`. Klik na řádek → UC-S03. (**Odchylka:** legacy zobrazoval jednu letenku na stránku s F10/F11; seznam plní stejný účel.)
- **Prázdný výsledek:** „No data match with this inserted information.“

#### UC-S03 Detail letenky a tisk palubní vstupenky (rekonstrukce pravé části `SRCHTK` + F12 → `PRINTCI`)

- **Zobrazení:** `TICKET ID`, jméno a příjmení, `CLIENT ID`, `FLIGHT NUM`, `FLIGHT DATE`, `TIME DEP`, `TIME LAND`, `AIRPORT DEP` + město, `AIRPORT LAND` + město, `SEAT`, odkaz na nákup (`BUYID`, datum, prodejce, celková cena).
- **Akce *Print boarding pass*:** otevře tiskovou stránku (HTML určené pro tisk, formát A5 nebo šířka 95 znaků monospace) s obsahem dle `TICKET-FORMAT`:
  - levá část: „BOARDING PASS – COBOL AIRLINES“, `PASSENGER NAME` (velkými písmeny), `SEAT`, `FROM: {CITY}-{AIRPORTDEP}`, `TO: {CITY}-{AIRPORTARR}`, `FLIGHT: {FLIGHTNUM} / DATE: {DDMMMYYYY} / DEPARTURE: {HH:MM}`;
  - pravá část (útržek): jméno, `FROM {DEP} TO {ARR}`, `FLIGHT`, `DATE` (ISO), `SEAT`.
  - Datum `DDMMMYYYY` používá anglické zkratky měsíců `JAN…DEC` (legacy tabulka `WS-DATE-VERIFY`).
- **Odchylka:** místo JES jobu vzniká tisknutelná stránka; hláška „Ticket printed“ se nahrazuje otevřením stránky. Volitelně export PDF (nepovinné).

#### UC-S04 Seznam a hledání cestujících (návrh, náhrada za neimplementované F7 „PASS REG.“)

- **Vstupy filtru:** `CLIENT ID`, `LAST NAME` (začíná na, bez ohledu na velikost písmen), `FIRST NAME` (dtto), `EMAIL` (obsahuje). Bez filtru se zobrazí prvních 10 podle `LASTNAME, FIRSTNAME`.
- **Výstup:** `CLIENT ID`, `LAST NAME`, `FIRST NAME`, `CITY`, `COUNTRY`, `TELEPHONE`, `EMAIL`; odkaz na detail a editaci; tlačítko *New passenger*.
- **Detail cestujícího:** všechna pole + seznam jeho letenek (odkaz na UC-S03).

#### UC-S05 Registrace a editace cestujícího (návrh na základě tabulky `PASSENGERS`)

- **Pole:** `FIRST NAME` (1–30, povinné), `LAST NAME` (1–30, povinné), `ADDRESS` (1–250, povinné), `CITY` (1–50, povinné), `COUNTRY` (1–30, povinné), `ZIPCODE` (1–15, povinné), `TELEPHONE` (1–18, povinné, povolené znaky číslice, mezera, `+`, `-`), `EMAIL` (1–100, povinné, syntakticky platný e-mail).
- **Pravidla:** `CLIENTID` přiděluje systém; jména se ukládají tak, jak byla zadána, s oříznutím okrajových mezer (**Odchylka:** legacy data jsou velkými písmeny; hledání je case-insensitive, takže smíšená data nevadí; palubní vstupenka tiskne velkými písmeny). Duplicitní e-mail je varování, ne chyba (legacy nemá unique).
- **Výstup:** po uložení přesměrování na detail s hláškou „Passenger {CLIENTID} saved.“

#### UC-S06 Prodej letenek – krok 1: výběr letu a klienta (rekonstrukce `SELLCOB1`, mapa `SELLMP`)

- **Vstupy:** `CLIENT ID` (číslo, povinné), `FLIGHT NUM` (6, povinné), `DATE` (ISO, povinné), `PASS NUMBER` (1–9, povinné). Pole lze předvyplnit z UC-S01 (query parametry) nebo z UC-S04.
- **Validace (v legacy pořadí, zobrazí se všechny nalezené chyby – Odchylka):**
  1. `CLIENT ID` číslo > 0 → „You must insert a number in the client id.“
  2. `FLIGHT NUM` neprázdné → „You must insert a correct flight number.“
  3. `DATE` ISO → „The correct date format is: YYYY-MM-DD.“
  4. `PASS NUMBER` 1–9 → „You must insert a number in the number of clients.“
- **Kontroly dat:**
  5. Klient existuje → jinak „This passenger does not exist.“
  6. Let s `FLIGHTNUM` + `FLIGHTDATE` existuje → jinak „This flight does not exist.“
  7. Let není v minulosti (`FLIGHTDATE >= dnes`) → jinak „This flight has already departed.“ (**návrh**)
  8. Volná místa ≥ `PASS NUMBER` → jinak „Not enough free seats on this flight ({n} left).“ (**návrh**; legacy nekontroloval)
- **Výstup (rekapitulace vpravo):** `FLIGHT NUM`, `DATE`, `DEP TIME`, `LAND TIME`, `DEP AIRPORT`, `LAND AIRPORT`, `PRICE` (cena za osobu = `FLIGHT.PRICE`, výchozí 120.99), `TOTAL PRICE = PRICE × PASS NUMBER`, jméno klienta. Tlačítko *Insert passengers* (F12) → UC-S07. Stav prodeje se drží v session (ekvivalent COMMAREA 66 B) nebo jako skryté parametry formuláře.

#### UC-S07 Prodej letenek – krok 2: cestující a potvrzení (rekonstrukce `SELLCOB2` z mapy `SELLMP2` a snímků; zápis do DB je návrh)

- **Zobrazení:** vlevo rekapitulace z kroku 1 (`CLIENT ID`, `FLIGHT NUM`, `AIRPORT DEP`, `AIRPORT LAND`, `DATE`, `PASS NUMBER`, `PRICE`, `TOT PRICE`), vpravo `PASS NUMBER` řádků `CLIENTID: [____] NAME: ______`. Řádek 1 předvyplněn objednávajícím klientem (lze změnit).
- **Dohledání jmen:** po zadání `CLIENTID` (změna pole nebo tlačítko *Check*) se zobrazí jméno nebo „Passenger {id} does not exist.“
- **Akce *Return* (F10/F11):** zpět na krok 1 se zachovanými hodnotami.
- **Akce *Confirm passengers* (F12):**
  1. Validace: všechna ID vyplněna, existují, jsou navzájem různá (**návrh**; jeden člověk nemůže mít dvě sedadla), žádný z nich nemá na tomto letu už letenku („Passenger {id} already has a ticket on this flight.“ – **návrh**).
  2. Znovu ověřit kapacitu (souběh) – v transakci se zámkem řádku letu.
  3. Vytvořit `BUY`: `BUYDATE`, `BUYTIME` = teď (`Europe/Paris`), `PRICE` = celková cena, `EMPID` = přihlášený uživatel, `CLIENTID` = objednávající (řádek 1).
  4. Pro každého cestujícího vytvořit `TICKET`: `TICKETID` ze sekvence, `BUYID`, `CLIENTID`, `FLIGHTID`, `SEAT` = první volné sedadlo (kap. 5.2).
  5. Přesměrovat na stránku potvrzení (UC-S08).
- **Chybové stavy:** kapacita vyčerpána mezi krokem 1 a potvrzením → „Not enough free seats on this flight ({n} left).“ a návrat na krok 2; DB chyba → obecná hláška.

#### UC-S08 Potvrzení prodeje a účtenka (rekonstrukce `PRINTPA`, `RECEIPT-FORMAT`)

- **Zobrazení:** „Sale {BUYID} completed.“, seznam vytvořených letenek (`TICKET ID`, cestující, `SEAT`) s odkazy na detail (UC-S03) a hromadný tisk palubních vstupenek; tlačítko *Print receipt*.
- **Účtenka (tisková stránka):** „RECEIPT“, `BUYID`, `CB/CS/CH` (typ platby – v originálu neimplementováno; zobrazit „Payment: not recorded“), „Le {DD/MM/YYYY} a {HH:MM:SS}“ (datum/čas nákupu; legacy tiskl čas tisku), „COBOL AIRLINES / PARIS / 75000“, maskované číslo karty `**********`, „MONTANT = {PRICE} EUR“, „DEBIT/CREDIT“, „TICKET CLIENT – TO KEEP“.
- **Přístup:** účtenku lze znovu otevřít z detailu letenky (odkaz na nákup).

#### UC-S09 Detail nákupu (návrh)

- `BUYID`, datum a čas, prodejce (`EMPID` + jméno), objednávající klient, celková cena, seznam letenek, tlačítko *Print receipt*. Storno není v rozsahu (legacy neřeší; `ON DELETE RESTRICT` naznačuje, že mazání nebylo zamýšleno).

### 3.3 IT Support (návrh)

#### UC-I01 Správa uživatelských účtů

- Seznam zaměstnanců s `EMPID`, jménem, oddělením, stavem účtu (aktivní / neaktivní / bez hesla), datem posledního přihlášení.
- Akce: *Reset password* (vygeneruje dočasné heslo, zobrazí ho jednou; uživatel je při dalším přihlášení vyzván ke změně), *Deactivate* / *Activate*.
- Účet vzniká automaticky při založení zaměstnance (UC-H01) ve stavu „bez hesla“.

#### UC-I02 Číselník letišť

- CRUD nad `AIRPORT`: `AIRPORTID` (3–4 znaky, velká písmena, unikátní, po založení needitovatelné), `NAME` (100), `ADDRESS` (250), `CITY` (30), `COUNTRY` (30), `ZIPCODE` (15). Smazání jen bez navázaných letů (jinak „Airport is used by {n} flights.“).

#### UC-I03 Číselník letadel

- CRUD nad `AIRPLANE`: `AIRPLANEID` (8, unikátní), `TYPE` (8), `NUMSEATS` (1–999), `TOTALFUEL` (≥ 0). Smazání jen bez navázaných letů. Změna `NUMSEATS` pod počet prodaných letenek na některém letu je chyba.

### 3.4 HR (návrh podle tabulek `EMPLO`, `DEPT`)

#### UC-H01 Zaměstnanci

- Seznam s filtrem (jméno, oddělení), 10 na stránku.
- Založení/editace: `EMPID` (8 číslic; při založení navrženo jako max + 1, editovatelné, unikátní), `FIRST NAME` (30), `LAST NAME` (30), `ADDRESS` (100), `CITY` (50), `ZIPCODE` (15), `TELEPHONE` (10–20), `EMAIL` (100, platný), `ADMIDATE` (ISO, ne v budoucnosti), `SALARY` (0–999999.99), `DEPTID` (výběr). Vše povinné.
- Smazání se nepovoluje (FK `RESTRICT` z `BUY`, `CREW`, `DEPT.MANAGER`); místo něj deaktivace účtu (UC-I01).

#### UC-H02 Oddělení

- Seznam `DEPT` (`DEPTID`, `NAME`, `MANAGER`), editace názvu a manažera (výběr ze zaměstnanců daného oddělení). Nová oddělení se nezakládají (role jsou svázané s `DEPTID` 1–9).

### 3.5 Schedule (návrh podle tabulek `FLIGHT`, `CREW`, `SHIFT` a programu `CBFLIGHT`)

#### UC-P01 Lety – seznam a editace

- Seznam letů s filtrem (datum od–do, číslo letu, letiště), sloupce jako UC-S01 + letadlo, směna, prodané letenky.
- Založení/editace: `FLIGHTNUM` (`CB` + 4 číslice), `FLIGHTDATE`, `DEPTIME`, `ARRTIME`, `AIRPLANEID`, `AIRPORTDEP`, `AIRPORTARR` (≠ odlet), `SHIFTID`, `PRICE` (výchozí 120.99). `TOTPASS` se nastaví na `NUMSEATS` letadla, `TOTBAGGA` = 0 (rekonstrukce `UPDATE1`).
- Unikátnost `FLIGHTNUM` + `FLIGHTDATE`.
- Smazání jen bez letenek.

#### UC-P02 Generování letů na období (rekonstrukce `CBFLIGHT`)

- Vstupy: vzorový let (výběr), období od–do (max. 92 dní), dny v týdnu (výchozí všechny).
- Výsledek: pro každý den v období, kde ještě neexistuje let s tímto `FLIGHTNUM`, vznikne kopie vzoru (stejné časy, letadlo, letiště, směna, cena). Zobrazí se počet vytvořených a přeskočených.

#### UC-P03 Posádky

- CRUD nad `CREW`: 6 členů (`COMMANDER` z `DEPTID 2`, `COPILOTE` z `3`, `FACHIEF` + `FLIATTENDANT1..3` z `4`), všichni různí. Smazání jen bez směn.

#### UC-P04 Směny

- CRUD nad `SHIFT`: `SHIFTDATE`, `BEGINTIME` < `ENDTIME`, `CREWID`. Seznam s filtrem podle data a posádky. Smazání jen bez letů.

### 3.6 Air Staff (`crew`, návrh)

#### UC-C01 Moje směny a lety

- Read-only seznam směn, kde je přihlášený zaměstnanec členem posádky (od dneška dál, řazeno podle data), a k nim lety (`FLIGHTNUM`, trasa, časy, letadlo, počet cestujících). Bez editace.

### 3.7 CEO (návrh)

#### UC-E01 Přehledy

- Karty: počet prodejů a tržby za zvolené období (výchozí aktuální měsíc), počet letenek, průměrná obsazenost letů, TOP 5 tras. Tabulka prodejů podle prodejce. Pouze čtení. Součty z `BUY.PRICE` a `TICKET`.

### 3.8 Legal

- Pouze UC-A01–A04 a domovská stránka „The legal functions are not available yet.“

## 4. Obrazovky

### 4.1 Mapování legacy obrazovek → web

| Legacy | Web (URL) | Use case |
|---|---|---|
| `LOGON` (`LOGINMP`) | `/login/` | UC-A01 |
| F3 | `/logout/` | UC-A02 |
| – | `/password/` | UC-A03 |
| větvení v `LOGIN` | `/` (domovská stránka role) | UC-A04 |
| `SRCHPA` (`SRCHFLI`) | `/sales/flights/` | UC-S01 |
| `SRCHTK` (`SRCHTKT`) – levá část | `/sales/tickets/` | UC-S02 |
| `SRCHTK` – pravá část + F12 | `/sales/tickets/<ticketid>/`, `/sales/tickets/<ticketid>/boarding-pass/` | UC-S03 |
| F7 „PASS REG.“ (neexistovalo) | `/sales/passengers/`, `/sales/passengers/<clientid>/` | UC-S04 |
| – | `/sales/passengers/new/`, `/sales/passengers/<clientid>/edit/` | UC-S05 |
| `SELLMP` (`SELLMS`) | `/sales/sell/` | UC-S06 |
| `SELLMP2` (`SELLMS2`) | `/sales/sell/passengers/` | UC-S07 |
| `PRINTPA` | `/sales/buys/<buyid>/`, `/sales/buys/<buyid>/receipt/` | UC-S08, UC-S09 |
| – | `/it/users/`, `/it/airports/`, `/it/airplanes/` | UC-I01–I03 |
| – | `/hr/employees/`, `/hr/departments/` | UC-H01–H02 |
| – | `/schedule/flights/`, `/schedule/flights/generate/`, `/schedule/crews/`, `/schedule/shifts/` | UC-P01–P04 |
| – | `/crew/my-shifts/` | UC-C01 |
| – | `/ceo/dashboard/` | UC-E01 |

### 4.2 Domovské stránky rolí

| Role | Po přihlášení |
|---|---|
| sales | `/sales/flights/` (rekonstrukce: `LOGIN` → `SRCHFLY`) |
| it | `/it/users/` |
| hr | `/hr/employees/` |
| schedule | `/schedule/flights/` |
| crew | `/crew/my-shifts/` |
| ceo | `/ceo/dashboard/` |
| legal | `/` s hláškou |

### 4.3 Detailní popis obrazovek Sales

#### S-LOGIN `/login/`

| Pole | Typ | Délka | Povinné | Validace |
|---|---|---|---|---|
| `USERID` | text | 8 | ano | neprázdné |
| `PASSWORD` | password | – | ano | neprázdné |

Akce: *Login*. Hlášky: „Password or userid incorrect.“; „You have been logged out.“; „Welcome to COBOL AIRLINES system“ (úvodní text legacy).

#### S-FLIGHTS `/sales/flights/` (GET s query parametry, formulář nahoře, výsledky pod ním)

| Pole | Typ | Délka | Povinné | Validace / hláška |
|---|---|---|---|---|
| `FLIGHT NUM` | text | 6 | ne | – |
| `DATE` | date | 10 | ne | ISO / „Wrong date format, try to insert date as YYYY-MM-DD“ |
| `DEP AIRPORT` | text | 4 | ne | 3–4 znaky |
| `LAND AIRPORT` | text | 4 | ne | 3–4 znaky |

Souhrnná validace: alespoň jedno pole / „No data inserted, try again.“ Výstup: tabulka kap. UC-S01, stránkování. Řádek má odkaz *Sell* → `/sales/sell/?flightnum=…&date=…`.

#### S-TICKETS `/sales/tickets/`

| Pole | Typ | Délka | Povinné | Validace |
|---|---|---|---|---|
| `TICKET ID` | text | 10 | ne | formát `CB\d{8}` |
| `CLIENT ID` | číslo | 10 | ne | celé > 0 |
| `FIRST NAME` | text | 30 | ne | – |
| `LAST NAME` | text | 30 | ne | – |
| `FLIGHT NUM` | text | 6 | ne | – |
| `FLIGHT DATE` | date | 10 | ne | ISO |

Souhrnná validace dle UC-S02 bod 4. Výstup: tabulka, řádek → `/sales/tickets/<ticketid>/`.

#### S-TICKET-DETAIL `/sales/tickets/<ticketid>/`

Read-only; 404 pro neexistující ID („Ticket not found“). Tlačítka: *Print boarding pass* (nová záložka), *Back to search*, odkaz na nákup.

#### S-BOARDING-PASS `/sales/tickets/<ticketid>/boarding-pass/`

Tisková stránka bez menu, `@media print` bez hlavičky; obsah dle UC-S03; tlačítko *Print* volá `window.print()`.

#### S-PASSENGERS `/sales/passengers/`

Filtr (`CLIENT ID`, `LAST NAME`, `FIRST NAME`, `EMAIL`), tabulka, *New passenger*.

#### S-PASSENGER-FORM `/sales/passengers/new/`, `/sales/passengers/<clientid>/edit/`

Pole a validace dle UC-S05. Tlačítka *Save*, *Cancel*.

#### S-PASSENGER-DETAIL `/sales/passengers/<clientid>/`

Všechna pole, tabulka letenek cestujícího (`TICKET ID`, `FLIGHT NUM`, `DATE`, trasa, `SEAT`), tlačítka *Edit*, *Sell ticket* (předvyplní `CLIENT ID`).

#### S-SELL-1 `/sales/sell/`

| Pole | Typ | Délka | Povinné | Hláška při chybě |
|---|---|---|---|---|
| `CLIENT ID` | číslo | 6 (legacy) → bez limitu | ano | „You must insert a number in the client id.“ |
| `FLIGHT NUM` | text | 6 | ano | „You must insert a correct flight number.“ |
| `DATE` | date | 10 | ano | „The correct date format is: YYYY-MM-DD.“ |
| `PASS NUMBER` | číslo | 1 | ano | „You must insert a number in the number of clients.“ (1–9) |

Po úspěšném *Research* (Enter) se vpravo zobrazí rekapitulace a tlačítko *Insert passengers*. Bez úspěšného hledání je tlačítko neaktivní; pokus o přímý přístup na krok 2 bez stavu → „You need to make a valid research before going to the sell screen.“ a přesměrování na krok 1.

#### S-SELL-2 `/sales/sell/passengers/`

Rekapitulace + `PASS NUMBER` řádků (`CLIENTID` číslo, `NAME` read-only). Tlačítka *Check names*, *Return*, *Confirm passengers*. Chyby dle UC-S07.

#### S-SALE-DONE `/sales/buys/<buyid>/`

Dle UC-S08/S09. Tlačítka *Print receipt* (`/sales/buys/<buyid>/receipt/`), *Print all boarding passes* (`/sales/buys/<buyid>/boarding-passes/`), *New sale*.

### 4.4 Obrazovky ostatních rolí

Standardní CRUD vzor: seznam s filtrem a stránkováním → detail/formulář → uložení s hláškou „{Entity} {id} saved.“ / smazání s potvrzením „Delete {entity} {id}?“ a hláškou o vazbách. Pole a validace dle use cases 3.3–3.7. Konkrétní rozvržení určí implementace s dodržením společných prvků kap. 2.

## 5. Datová a výpočetní pravidla

### 5.1 Cena

- `FLIGHT.PRICE` (nový sloupec, `numeric(7,2)`, výchozí `120.99`) = cena za jednu letenku.
- `BUY.PRICE = FLIGHT.PRICE × počet letenek` v okamžiku prodeje; pozdější změna ceny letu neovlivní starý nákup.
- Bez slev, tříd a poplatků (legacy nemá).

### 5.2 Sedadla

- Kabina letadla: řady `1..ceil(NUMSEATS / 6)`, písmena `A–F`; sedadlo `{písmeno}{řada:02d}` (legacy vzor `B04`). Poslední řada může být neúplná (`NUMSEATS mod 6`).
- Přidělení: první volné sedadlo v pořadí řada 1 `A…F`, řada 2 `A…F`, … Cestující z jednoho nákupu dostanou sousední sedadla, pokud jsou volná (**návrh**).
- Unikátnost `(FLIGHTID, SEAT)`.

### 5.3 Kapacita a „PLACES“

- Volná místa letu = `AIRPLANE.NUMSEATS − počet TICKET pro FLIGHTID`. Sloupec `PLACES` v UC-S01 zobrazuje tuto hodnotu (legacy zobrazoval `TOTPASS`, který `UPDATE1` nastavil na `NUMSEATS`, tj. výchozí stav „vše volné“).
- `FLIGHT.TOTPASS` se ponechává jako kapacita letu (kopie `NUMSEATS` při založení letu), `TOTBAGGA` jako informativní (výchozí 0). Neaktualizují se při prodeji.

### 5.4 Identifikátory

- `TICKETID`: `'CB' || lpad(nextval('ticket_seq'), 8, '0')`.
- `EMPID`: 8 číslic; import z legacy zachovává hodnoty.
- `CLIENTID`, `BUYID`, `FLIGHTID`, `CREWID`, `SHIFTID`: identity.

### 5.5 Datum a čas

- Uloženo bez zóny (`date`, `time`) jako v DB2; `BUYDATE`/`BUYTIME` se plní lokálním časem `Europe/Paris`.
- „Dnes“ ve vyhledávání = dnešní datum v `Europe/Paris`.

### 5.6 Hesla

- Hash Argon2 nebo PBKDF2 (framework). Legacy hashe se nepřenášejí.
- Seed vývojové DB nastaví hesla z `EMPLOYEE-LIST.json` (otevřený tvar), aby šlo přihlásit historické účty (např. `10000006` / `kxXRk7GIHw`). V produkčním importu se hesla negenerují; IT je resetuje (UC-I01).

## 6. Chybové stavy – souhrn hlášek

| Kód | Text (EN) | Kde |
|---|---|---|
| E-AUTH-01 | Password or userid incorrect. | UC-A01 |
| E-AUTH-02 | You are not allowed to access this function. | všude (403) |
| E-SYS-01 | Communication error between system and DB, call IT dept. Error: {code} | všude (500) |
| E-FLT-01 | No data inserted, try again. | UC-S01 |
| E-FLT-02 | Wrong date format, try to insert date as YYYY-MM-DD | UC-S01, S02, S06 |
| E-FLT-03 | No flight matches the inserted information. | UC-S01 |
| E-TKT-01 | A valid research must have at least: ticket id, or client id, or client's first and last name. | UC-S02 |
| E-TKT-02 | No data match with this inserted information. | UC-S02 |
| E-TKT-03 | Ticket not found. | UC-S03 |
| E-SEL-01 | You must insert a number in the client id. | UC-S06 |
| E-SEL-02 | You must insert a correct flight number. | UC-S06 |
| E-SEL-03 | The correct date format is: YYYY-MM-DD. | UC-S06 |
| E-SEL-04 | You must insert a number in the number of clients. | UC-S06 |
| E-SEL-05 | This passenger does not exist. | UC-S06, S07 |
| E-SEL-06 | This flight does not exist. | UC-S06 |
| E-SEL-07 | This flight has already departed. | UC-S06 |
| E-SEL-08 | Not enough free seats on this flight ({n} left). | UC-S06, S07 |
| E-SEL-09 | You need to make a valid research before going to the sell screen. | UC-S07 |
| E-SEL-10 | Passenger {id} already has a ticket on this flight. | UC-S07 |
| E-SEL-11 | Passenger {id} is listed more than once. | UC-S07 |
| E-REF-01 | {Entity} is used by {n} {related}. | mazání číselníků |

## 7. Nefunkční požadavky (minimum pro PoC)

- Spuštění lokálně jedním příkazem (`docker compose up`), viz architektura.
- Odezva vyhledávání do 1 s nad seed daty (stovky letů, tisíce letenek); indexy na `FLIGHT(FLIGHTDATE, FLIGHTNUM)`, `TICKET(CLIENTID)`, `TICKET(FLIGHTID)`, `PASSENGERS(LASTNAME, FIRSTNAME)`.
- Všechny zápisy v transakcích; prodej používá zámek řádku letu.
- Přístup pouze pro přihlášené; CSRF ochrana formulářů; hesla hashovaná.
- Logování prodejů (kdo, kdy, co) do aplikačního logu.
- Testy: unit pro pravidla kap. 5 a validace kap. 3; e2e pro tok Sales (přihlášení → hledání letu → prodej → účtenka → hledání letenky → palubní vstupenka).

## 8. Otevřené body (rozhodnutí přijatá v této specifikaci)

| # | Otázka | Rozhodnutí |
|---|---|---|
| 1 | Chování `SELLCOB2` při potvrzení | Kap. UC-S07 (BUY + N × TICKET, sedadla automaticky, kontrola kapacity) |
| 2 | Cena | `FLIGHT.PRICE`, výchozí 120.99 EUR |
| 3 | Formát sedadla a přidělování | Kap. 5.2 |
| 4 | Hesla | Nový hash; seed z JSON pro vývoj |
| 5 | Hledání jmen | Case-insensitive, celé jméno (letenky) / prefix (cestující) |
| 6 | Stránkování letenek | Seznam místo „jedna letenka na stránku“ |
| 7 | F-klávesy | Menu a odkazy; bez F-kláves |
| 8 | Role bez obrazovek | Návrhy kap. 3.3–3.7; priorita až po Sales |
| 9 | Storno nákupu / letenky | Mimo rozsah v1 |
| 10 | Vícejazyčnost | Mimo rozsah; UI anglicky |
