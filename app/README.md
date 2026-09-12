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

## Structure

The Django project is in `config/`, application modules are in `accounts/` and `core/`, shared
templates and static assets are in `templates/` and `static/`, and automated checks are in
`tests/`. See [the target architecture](../docs/rewrite/03-target-architecture.md) for the planned
full structure.

## Environment

Copy `.env.example` to `.env` to configure `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`,
`DATABASE_URL`, and `LEGACY_ROOT`. Compose supplies development-safe defaults automatically.

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
