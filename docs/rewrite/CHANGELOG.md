# CHANGELOG přepisu

Každý PR do `rewrite` přidává záznam na začátek souboru (nejnovější nahoře). Formát viz `AGENTS.md` kap. 5.

## R24 – Kontrakt validace formulářů a testy neplatných cest
- PR: #54 (codex/R24-form-validation)
- Přidáno: konkrétní view testy validačních hlášek a zachování databáze pro všechny formulářové obrazovky, včetně hledání.
- Změněno: `SearchListView` hlásí chyby přes `report_form_errors` a nedědí nepoužívaný formulářový mixin.
- Odchylky od specifikace: žádné.

## R23 – Docstringy a vazba na legacy
- PR: #52 (codex/R23-docstrings)
- Přidáno: docstringy modulů, tříd a veřejných funkcí s odkazem na legacy program, mapu, tabulku DB2 a use case; test `tests/unit/test_docstrings.py` hlídá pokrytí i šablonové formulace.
- Změněno: `role_required` má anglický docstring; komentáře `#` u pravidel, která z kódu nejsou zřejmá.
- Odchylky od specifikace: žádné.

## R22 – Závěr refaktoringu: úklid, testy, dokumentace
- PR: #50 (codex/R22-refactor-cleanup)
- Přidáno: kanonické URL modelů a úplná matice oprávnění pro všechny aplikační URL a role.
- Změněno: duplicitní testy oprávnění nahradila matice; testovací helpery nahradily sdílené fixtures a README popisuje přidání obrazovky.
- Odchylky od specifikace: žádné.

## R21 – Sales a Reports na generických views
- PR: #48 (codex/R21-generic-sales)
- Přidáno: queryset API pro cestující, letenky a nákupy, filtry reportů a testy session a období.
- Změněno: Sales a Reports používají generické class-based views, sdílené formuláře, detailní a seznamové šablony.
- Odchylky od specifikace: `FlightSearchForm` zůstává běžný `forms.Form`, protože jeho validace vyžaduje alespoň jedno vyhledávací kritérium a semantika `FilterForm.value()` se nepoužívá.

## R20 – Schedule, HR a IT na generických views
- PR: #46 (codex/R20-generic-schedule-hr)
- Přidáno: doménové querysety, filtrovací formuláře a služby pro účty a založení zaměstnance.
- Změněno: Schedule, HR a IT používají generické class-based views a sdílené šablony.
- Odchylky od specifikace: žádné.

## R19 – Základ generického jádra
- PR: #44 (codex/R19-generic-core-v3)
- Přidáno: generické views a mixiny, filtrovací formulář, renderer, sdílené šablony a template tag stavu účtu.
- Změněno: aplikace fleet používá class-based views; navigace a oprávnění mají jedinou deklarativní konfiguraci.
- Odchylky od specifikace: žádné.

## R18 – Hardening a závěr
- PR: #41 (codex/R18-hardening)
- Přidáno: limiter přihlášení, produkční bezpečnostní nastavení, Gunicorn/WhiteNoise image, chybová stránka 500 a testy navigace a chybových stránek.
- Změněno: 404 stránka, auditní logování autentizace a prodejů a provozní dokumentace.
- Odchylky od specifikace: E2E testy nebyly v Codex sandboxu spuštěny podle zadání issue; ověří je Claude lokálně.

## R17 – Crew „My shifts“ a CEO dashboard
- PR: #39 (codex/R17-crew-ceo)
- Přidáno: přehled vlastních směn posádky a agregovaný CEO dashboard s filtrem období.
- Změněno: domovské stránky a navigace rolí Crew a CEO.
- Odchylky od specifikace: žádné.

## R16b – Schedule: posádky a směny
- PR: #37 (codex/R16b-schedule-crews)
- Přidáno: správa posádek a směn, filtrování a stránkování směn, validace rolí členů a překryvů a testy oprávnění.
- Změněno: navigace role Schedule obsahuje odkazy na posádky a směny.
- Odchylky od specifikace: žádné.

## R16a – Schedule: lety a generování na období
- PR: #35 (codex/R16a-schedule-flights)
- Přidáno: správa letů, filtrování a stránkování, generování letů na období a testy formulářů, služby a oprávnění.
- Změněno: seed používá sdílený generátor z aplikace operations a role Schedule má domovskou stránku a navigaci letů.
- Odchylky od specifikace: žádné.

## R15 – HR: zaměstnanci a oddělení
- PR: #33 (codex/R15-hr)
- Přidáno: HR seznam, detail a formuláře zaměstnanců a správa názvů a manažerů oddělení s testy oprávnění.
- Změněno: navigace rolí HR a CEO a sdílené automatické vytváření uživatelského účtu zaměstnance.
- Odchylky od specifikace: žádné.

## R14 – Import z exportu DB2
- PR: #31 (codex/R14-import-legacy)
- Přidáno: atomický a idempotentní import DB2 DEL souborů, JSON report, dry-run, normalizace a testovací exporty.
- Změněno: sdílené legacy parsery nově zpracovávají explicitní formáty data a času; README popisuje export a obnovu účtů.
- Odchylky od specifikace: žádné.

## R13 – IT Support: uživatelské účty, letiště, letadla
- PR: #29 (codex/R13-it-support)
- Přidáno: správa účtů zaměstnanců a CRUD letišť a letadel včetně validací, oprávnění a testů.
- Změněno: navigace rolí IT a Schedule o nové administrační obrazovky.
- Odchylky od specifikace: žádné.

## R12 – E2E testy toku Sales
- PR: #27 (codex/R12-e2e-sales)
- Přidáno: Playwright testy přihlášení rolí, kompletního prodeje, tisku, hledání letenky a správy cestujícího.
- Změněno: samostatný E2E marker a Compose/Make příkaz; běžná testovací sada E2E testy vynechává.
- Odchylky od specifikace: při opakovaném běhu test vybere první volný let CB1104 v okně dnes + 1 až 14 dní (preferuje dnes + 7).

## R11 – Sales: účtenka a hromadný tisk palubních vstupenek
- PR: #25 (codex/R11-receipt)
- Přidáno: tisková stránka účtenky a hromadný tisk všech palubních vstupenek nákupu s testy.
- Změněno: palubní vstupenka používá sdílenou šablonu a detail nákupu odkazuje na pojmenované tiskové URL.
- Odchylky od specifikace: žádné.

## R10 – Sales: prodej – krok 2 a potvrzení
- PR: #23 (codex/R10-sell-confirm)
- Přidáno: výběr a kontrola cestujících, bezpečné přidělení sedadel, atomické potvrzení prodeje a detail nákupu včetně testů.
- Změněno: detail letenky odkazuje na detail dokončeného nákupu.
- Odchylky od specifikace: žádné.

## R09 – Sales: prodej – krok 1
- PR: #21 (codex/R09-sell-step1)
- Přidáno: výběr letu a klienta, výpočet ceny a kapacity, rekapitulace a placeholder kroku cestujících včetně testů.
- Změněno: odkazy Sell nyní předvyplňují formulář a navigace role Sales obsahuje položku Sell.
- Odchylky od specifikace: žádné.

## R08 – Sales: cestující
- PR: #19 (codex/R08-passengers)
- Přidáno: filtrování, seznam, detail, založení a editace cestujících včetně validačních a view testů.
- Změněno: navigace role Sales obsahuje položku Passengers.
- Odchylky od specifikace: žádné.

## R07 – Sales: tisk palubní vstupenky
- PR: #17 (codex/R07-boarding-pass)
- Přidáno: služba formátování dat a samostatná tisková stránka palubní vstupenky s testy.
- Změněno: detail letenky nyní otevírá palubní vstupenku v nové záložce.
- Odchylky od specifikace: žádné.

## R06 – Sales: hledání letenek a detail
- PR: #15 (codex/R06-search-tickets)
- Přidáno: prioritní hledání letenek, stránkované výsledky a detail letenky včetně nákupu.
- Změněno: navigace rolí Sales a CEO a vlastní stránka 404.
- Odchylky od specifikace: žádné.

## R05 – Sales: hledání letů
- PR: #13 (codex/R05-search-flights)
- Přidáno: služba a formulář hledání letů, role-based obrazovka výsledků a sdílené stránkování.
- Změněno: domovská stránka a navigace role Sales; menu rolí CEO, Schedule a Crew.
- Odchylky od specifikace: žádné.

## R04 – Autentizace, role, kostra navigace
- PR: #11 (codex/R04-auth-roles)
- Přidáno: přihlášení, odhlášení, změna hesla, vynucená změna hesla, role-based oprávnění a navigace.
- Změněno: domovská stránka podle role, společná hlavička, katalog hlášek a dokumentace přihlášení.
- Odchylky od specifikace: žádné.

## R03 – Seed vývojových dat z legacy souborů
- PR: #9 (codex/R03-seed-demo)
- Přidáno: parsery legacy JSON/XML, idempotentní seed služby, příkaz `seed_demo` a testovací fixtures/testy.
- Změněno: dokumentace vývojových účtů a konfigurace aplikace `legacy_import`.
- Odchylky od specifikace: žádné.

## R02 – Datové schéma legacy tabulek
- PR: #7 (codex/R02-schema)
- Přidáno: Django modely legacy tabulek, databázové constraints a indexy, sekvence letenek, admin registrace, factories a testy schématu.
- Změněno: aplikace `accounts` rozšířena o oddělení, zaměstnance a mapování rolí; přidány aplikace `fleet`, `operations` a `sales`.
- Odchylky od specifikace: žádné.

## R01 – Scaffolding projektu, Docker Compose, tooling
- PR: #5 (codex/R01-scaffolding)
- Přidáno: Django projekt, aplikace `accounts` a `core`, Docker Compose, Makefile, vendorovaná statika a základní testy.
- Změněno: nic v legacy souborech.
- Odchylky od specifikace: žádné.

## R00c – Zadání R04–R08, předávání přes GitHub Issues
- Commit přímo do `rewrite`
- Přidáno: `codex-tasks/R04.md`–`R08.md`.
- Změněno: `AGENTS.md` kap. 0 (issue + `@codex`, labely `codex-task`, `step:R<ID>`, `needs-review`, `changes-requested`, `approved`), `CLAUDE.md` (postup zadávání, smoke test, review → merge).

## R00b – Zadání pro Codex R01–R03, proces merge
- Commit přímo do `rewrite` (schváleno uživatelem)
- Přidáno: `docs/rewrite/codex-tasks/R01.md`, `R02.md`, `R03.md` (samostatná zadání pro Codex Cloud).
- Změněno: `AGENTS.md` (odkaz na zadání, merge dělá Claude, fallback bez sítě/Dockeru), `CLAUDE.md` (merge a psaní zadání jako role, přímé commity dokumentace do `rewrite`), `03-target-architecture.md` kap. 4.2 (pojmenování FK polí), `04-migration-plan.md` (odkaz na zadání).
- Odchylky od specifikace: žádné.

## R00 – Analýza a dokumentace
- PR: #1 (claude/00-analysis-docs → rewrite)
- Přidáno: `docs/rewrite/01-inventory.md` (inventář legacy systému), `02-functional-spec.md` (funkční specifikace), `03-target-architecture.md` (cílová architektura), `04-migration-plan.md` (plán kroků R01–R18), `AGENTS.md` (pravidla pro Codex), `CLAUDE.md` (pravidla pro Claude), tento CHANGELOG.
- Změněno: nic v legacy souborech.
- Odchylky od specifikace: – (specifikace tímto PR vzniká; rozhodnutí o nejasných místech legacy jsou v `02-functional-spec.md` kap. 8).
