.PHONY: up down migrate seed test e2e lint check shell
COMPOSE ?= docker compose

up:
	$(COMPOSE) up -d db web

down:
	$(COMPOSE) down

migrate:
	$(COMPOSE) exec web python manage.py migrate

seed:
	$(COMPOSE) exec web python manage.py seed_demo

test:
	$(COMPOSE) exec web pytest -q tests/unit tests/views

e2e:
	$(COMPOSE) --profile e2e run --rm e2e

lint:
	$(COMPOSE) exec web sh -c "ruff check . && ruff format --check . && python manage.py check && python manage.py makemigrations --check --dry-run"

check: lint test

shell:
	$(COMPOSE) exec web python manage.py shell
