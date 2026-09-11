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

Demo data seeding will be added in R03. Authentication and login screens will be added in R04.
