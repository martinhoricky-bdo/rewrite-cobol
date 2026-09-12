# COBOL AIRLINES web application

## Requirements and quick start

Install Docker with the Compose plugin, then run:

```sh
cd app
make up
make migrate
```

Open <http://localhost:8000/>. Run all checks with `make check`, and stop the stack with
`make down`.

## Struktura kódu

Konfigurace Django projektu je v `config/`, doménové aplikace jsou v samostatných adresářích a sdílený kód je v `core/`.
Generické views a mixiny pro seznamy, hledání, formuláře a mazání jsou v `core/views/generic.py`.
Novou obrazovku přidejte jako class-based view složenou z Django generic view a odpovídajících mixinů.
Nastavte na ní model, formulář, povolené role, název stránky a pojmenované cílové URL.
Její pojmenovanou cestu zapište do `urls.py` příslušné aplikace.
Doménové dotazy patří do `QuerySet`/`Manager`, transakce do `services.py` a filtry do `FilterForm`.
Nakonec přidejte test view v `tests/views/` a záznam URL se všemi rolemi do `ROLE_MATRIX`.
HTML šablona rozšiřuje vhodnou sdílenou šablonu v `templates/core/`; vlastní šablonu vytvářejte jen pro obsah specifický pro obrazovku.

## Environment

Copy `.env.example` to `.env` to configure `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`,
`DATABASE_URL`, `LEGACY_ROOT`, `SECURE_SSL_REDIRECT`, and `SECURE_HSTS_SECONDS`. Compose supplies
development-safe defaults automatically. Login protection permits 10 failed attempts per
USERID and client IP in a 15-minute window; a successful login clears that counter. The counter
lives in the Django cache (`LocMemCache`, per process), so with several Gunicorn workers the limit
applies per worker; configure a shared cache backend if a strict global limit is required.

## Production

Build the production image with `docker build -t cobol-airlines .`. The image collects and
serves versioned static files with WhiteNoise, then starts three Gunicorn workers on port 8000:

```sh
docker run --env-file .env -p 8000:8000 cobol-airlines
```

Use a long random `SECRET_KEY`, the externally visible comma-separated `ALLOWED_HOSTS`, and the
PostgreSQL `DATABASE_URL`. Keep `SECURE_SSL_REDIRECT=True` when TLS terminates at the application
or a trusted reverse proxy; only disable it for an explicitly secured deployment topology. The
production settings enable secure session/CSRF cookies and one-year HSTS. Validate an environment
before deployment with `python manage.py check --deploy --settings=config.settings.prod`.

## Přihlášení

Po spuštění otevřete <http://localhost:8000/login/>. Přihlašovací údaje pro jednotlivé
role jsou uvedeny níže v sekci [Seed data](#seed-data). Přihlášený uživatel může změnit
heslo přes položku **Change password** a relaci ukončit přes **Logout**.

## Seed data

Run `make seed` after migrations to import the legacy demo data. The command is
idempotent; use `python manage.py seed_demo --flush` to remove and recreate seeded
application data. It also accepts `--from-date YYYY-MM-DD` and `--days N`.

Development logins are `10000006 / kxXRk7GIHw` (Sales), `10000029 / 8s1i3NL`
(CEO), `10000013 / VDNDY7xUpm25` (HR), `10000027 / 1jok1x` (IT),
`10000022 / 8I324l` (Schedule), `10000003 / 7bVHdRyqYD` (Crew), and
`10000017 / fijshQ3d` (Legal). These test passwords come from the legacy
repository and are for development only.

## E2E testy

Playwright scénáře se spouštějí proti běžícímu stacku naplněnému seed daty:

```sh
make up && make migrate && make seed && make e2e
```

Pro lokální spuštění bez Dockeru nejprve spusťte webový server, nainstalujte Chromium
pomocí `playwright install chromium` a v dalším terminálu spusťte:

```sh
BASE_URL=http://localhost:8000 pytest -m e2e tests/e2e
```

Běžné `pytest` a `make test` E2E scénáře automaticky vynechávají.

## Import z DB2

V DB2 vyexportujte tabulky `AIRPORT`, `AIRPLANE`, `DEPT`, `EMPLO`, `PASSENGERS`,
`CREW`, `SHIFT`, `FLIGHT`, `BUY` a `TICKET` do samostatných souborů, například:

```sql
EXPORT TO AIRPORT.csv OF DEL SELECT * FROM AIRPORT;
```

Soubory ponechte s velkými názvy a spusťte import s JSON reportem:

```sh
python manage.py import_legacy --dir /cesta/k/exportu --report /tmp/import-report.json
```

Pro americká data použijte `--date-format us`; před skutečným importem lze použít
`--dry-run`. Report po běhu zkontrolujte, zejména přeskočené řádky a chybějící
cizí klíče. Hesla se nemigrují: vytvořené účty jsou neaktivní, mají nepoužitelné
heslo a IT jim musí nastavit nové heslo a účet aktivovat.
