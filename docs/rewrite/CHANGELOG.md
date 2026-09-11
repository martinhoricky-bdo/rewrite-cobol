# CHANGELOG přepisu

Každý PR do `rewrite` přidává záznam na začátek souboru (nejnovější nahoře). Formát viz `AGENTS.md` kap. 5.

## R01 – Scaffolding projektu, Docker Compose, tooling
- PR: #TBD (codex/R01-scaffolding)
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
