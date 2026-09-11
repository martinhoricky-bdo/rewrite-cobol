# AGENTS.md – pravidla pro implementačního agenta (OpenAI Codex)

Tento repozitář je PoC přepisu legacy systému COBOL AIRLINES (COBOL + DB2 + CICS) na webovou aplikaci (Python/Django + PostgreSQL). Práce probíhá ve dvojici:

- **Claude** – analýza, návrh, review PR, údržba dokumentace v `docs/rewrite/`. Řídí se `CLAUDE.md`.
- **Codex (ty)** – implementace nové aplikace v `app/` po malých krocích definovaných v `docs/rewrite/04-migration-plan.md`.

Konkrétní zadání každého kroku je v **`docs/rewrite/codex-tasks/<ID>.md`** (např. `R01.md`). Zadání je samostatné a závazné; kde se liší od obecného plánu, platí zadání. Pokud zadání pro krok neexistuje, nezačínej – Claude ho nejdřív napíše.

Před první změnou si přečti v tomto pořadí: `docs/rewrite/04-migration-plan.md` (co dělat), `docs/rewrite/02-functional-spec.md` (jak se to má chovat), `docs/rewrite/03-target-architecture.md` (jak to postavit), `docs/rewrite/01-inventory.md` (odkud to pochází).

## 0. Předávání práce přes GitHub Issues (`@codex`)

- Každý krok dostaneš jako **GitHub Issue** v tomto repozitáři s názvem `R<ID>: <název kroku>` (např. `R01: scaffolding projektu, Docker Compose, tooling`), labely `codex-task` a `step:R<ID>`, tělem = obsah `docs/rewrite/codex-tasks/R<ID>.md` a komentářem se zmínkou `@codex`. Zmínka spouští tvůj Codex Cloud task.
- Pracuj jen na issue, kde jsi byl zmíněn. Jeden issue = jeden PR. V popisu PR uveď `Closes #<číslo issue>`; PR směřuje do `rewrite`.
- Pokud zadání v issue a soubor `docs/rewrite/codex-tasks/R<ID>.md` nesouhlasí, platí soubor v repozitáři (issue je jen jeho kopie) – rozdíl uveď v PR.
- Otázky k zadání piš jako komentář do issue (bez zmínky, nebo se zmínkou `@martinhoricky-bdo`), ne do kódu. Claude odpovídá v issue nebo upraví zadání.
- Labely na PR nastavuje Claude: `needs-review` (po otevření), `changes-requested` (po review s výhradami), `approved` (před merge). Ty labely neměníš.
- Po merge Claude zavře issue (nebo ho zavře `Closes #N`) a založí issue dalšího kroku. Nezačínej další krok bez issue se zmínkou.

## 1. Větve a cíl

- Cílová větev je **`rewrite`**. Nikdy nepushuj do `main` – `main` je původní COBOL a slouží jen jako reference.
- Pro každý krok založ větev **`codex/<ID>-<slug>`** z aktuální `rewrite`, např. `codex/R05-search-flights`. `<ID>` je identifikátor kroku z plánu (`R01`…`R18`, případně `R16a`).
- Jeden PR = jeden krok plánu. Nekombinuj kroky, nepřeskakuj závislosti uvedené v plánu. Je-li krok příliš velký, rozděl ho (`R16a`, `R16b`) a napiš to do popisu PR.
- PR směřuje do `rewrite`. Review a merge (squash) dělá Claude; větev po merge maže Claude. Další krok začínáš až po zmínce `@codex` v novém issue (kap. 0).

## 2. Co smíš a co nesmíš měnit

- **Nová aplikace žije výhradně v `app/`.** Vše (kód, Docker, Makefile, testy, statické soubory, README aplikace) patří tam.
- **Legacy adresáře jsou read-only:** `CICS/`, `COB-PROG/`, `DB2/`, `AS-400/`, `VIDEOS/` a kořenový `README.md`. Nikdy je neupravuj, nepřesouvej ani nemaž. Seed data z nich pouze čteš (přes `LEGACY_ROOT`).
- **`docs/rewrite/`** upravuj jen takto: přidej záznam do `CHANGELOG.md` (povinné) a případně opravu zjevné chyby v dokumentaci, kterou jsi při implementaci odhalil – takovou změnu vždy zvlášť vypiš v popisu PR. Změny specifikace a plánu navrhuj v PR jako „Otevřené otázky“, neprováděj je mlčky.
- **Zákaz GitHub Actions:** nevytvářej nic v `.github/workflows/` ani jiné CI konfigurace. Kontroly se spouštějí lokálně přes `make check`.
- Nepřidávej závislosti nad rámec `03-target-architecture.md` bez zdůvodnění v PR. Žádné CDN – statické soubory se vendorují do `app/static/`. Pokud prostředí nemá síť a soubor nelze stáhnout, vytvoř minimální náhradu a uveď to v PR jako odchylku.
- Prostředí bez Dockeru: `make` cíle lze nahradit přímými příkazy (`pip install -e .[dev]`, `DATABASE_URL` na lokální PostgreSQL, `pytest`, `ruff`). Uveď v PR, jak jsi kontroly spustil.
- Neukládej žádné tajemství do repozitáře (`.env` je v `.gitignore`; `.env.example` obsahuje jen ukázkové hodnoty).

## 3. Konvence kódu

- Python 3.12, Django 5.x, PostgreSQL 16. Struktura aplikací dle `03-target-architecture.md` kap. 3.
- Formátování a lint: `ruff` (konfigurace v `app/pyproject.toml`). Typové anotace u veřejných funkcí služeb.
- Business logika v `services.py` dané aplikace; views tenké; formuláře jako `django.forms.Form`/`ModelForm`.
- Názvy DB tabulek a sloupců = legacy názvy malými písmeny (`db_table`, `db_column`), názvy polí modelů stejné (`flightnum`, `airportdep`). Nepřejmenovávej.
- Texty v UI anglicky, hlášky doslova podle `02-functional-spec.md` kap. 6 (kódy `E-…`). V testech se na tyto texty odkazuj přes konstanty, ne opisem.
- Datum/čas: `TIME_ZONE = 'Europe/Paris'`, `USE_TZ = True`; „dnes“ vždy přes `timezone.localdate()`.
- Peníze jako `Decimal`, nikdy `float`.
- Commit message: `R05: search flights – form, service, view, tests` (ID kroku na začátku). Žádné identifikátory modelů AI v commitech ani v kódu.

## 4. Testy a lokální ověření

Referenční cesta je Docker Compose (`app/docker-compose.yml`):

```
cd app
make up          # db + web
make migrate
make seed        # seed_demo z legacy souborů (od R03)
make check       # ruff + django check + makemigrations --check + pytest (unit, views)
make e2e         # Playwright proti běžícímu stacku (od R12)
make down
```

Pravidla:

- Každá nová funkce má testy: unit (služby, validace) a view testy (Django test client: GET/POST, chybové hlášky, oprávnění rolí → 403). Testy na oprávnění jsou povinné u každé nové URL.
- Před otevřením PR musí `make check` projít; posledních ~10 řádků výstupu vlož do popisu PR. Pokud něco neprochází a nedokážeš to opravit, PR neotvírej jako hotový – označ ho jako draft a popiš problém.
- Testy nesmí záviset na síti ani na aktuálním datu bez fixace (`freezegun` nebo parametr `today`).
- Fixtures pro testy jsou malé (několik řádků), ne kopie celých legacy souborů.

## 5. Co musí obsahovat každý PR

1. Popis podle šablony v `04-migration-plan.md` (sekce „Šablona popisu PR“): ID a název kroku s odkazem na plán a na zadání `docs/rewrite/codex-tasks/<ID>.md`, co PR dělá, jak ověřit, výstup `make check`, odchylky/otevřené otázky, checklist.
2. Testy (viz kap. 4).
3. Migrace, pokud se mění schéma (`python manage.py makemigrations <app>` s popisným názvem, např. `0003_flight_price`). Žádné ruční úpravy vygenerovaných migrací bez komentáře proč.
4. Záznam v `docs/rewrite/CHANGELOG.md` ve formátu:

   ```
   ## R05 – Sales: hledání letů
   - PR: #<číslo> (codex/R05-search-flights)
   - Přidáno: …
   - Změněno: …
   - Odchylky od specifikace: žádné | …
   ```

5. Aktualizace `app/README.md`, pokud se mění způsob spuštění, příkazy nebo seed účty.

## 6. Když je specifikace nejasná

- Nejdřív hledej odpověď v `02-functional-spec.md` (včetně kap. 8 „Otevřené body“) a `01-inventory.md` kap. 9.
- Pokud odpověď není, zvol nejjednodušší řešení konzistentní s legacy chováním, implementuj ho a **výslovně** ho popiš v sekci „Odchylky od specifikace / otevřené otázky“ PR. Claude v review rozhodne a případně upraví dokumentaci.
- Nikdy nerozšiřuj rozsah kroku „při té příležitosti“. Nápady na vylepšení patří do popisu PR, ne do kódu.

## 7. Review a opravy

- Review dělá Claude. Připomínky řeš dalšími commity ve stejné větvi (bez force-push, bez rebase po zahájení review).
- Připomínku, se kterou nesouhlasíš, nezamlč – odpověz v PR s argumentem.
- Po merge pokračuj dalším krokem podle plánu a závislostí; před začátkem si vždy stáhni aktuální `rewrite`.
