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

Authentication and login screens will be added in R04.

## Seed data

Run `make seed` after migrations to import the legacy demo data. The command is
idempotent; use `python manage.py seed_demo --flush` to remove and recreate seeded
application data. It also accepts `--from-date YYYY-MM-DD` and `--days N`.

Development logins are `10000006 / kxXRk7GIHw` (Sales), `10000029 / 8s1i3NL`
(CEO), `10000013 / VDNDY7xUpm25` (HR), `10000027 / 1jok1x` (IT),
`10000022 / 8I324l` (Schedule), `10000003 / 7bVHdRyqYD` (Crew), and
`10000017 / fijshQ3d` (Legal). These test passwords come from the legacy
repository and are for development only.
