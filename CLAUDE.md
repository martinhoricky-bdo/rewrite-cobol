# CLAUDE.md – pravidla pro analytického a review agenta (Claude)

Repozitář: PoC přepisu legacy systému COBOL AIRLINES (COBOL + DB2 + CICS, větev `main` = originál, read-only) na webovou aplikaci Python/Django + PostgreSQL. Veškerý výstup jde do větve **`rewrite`**. Implementaci píše OpenAI Codex v samostatných PR (`codex/<ID>-<slug>`), ty děláš analýzu, návrh, review a udržuješ dokumentaci. Pravidla pro Codex jsou v `AGENTS.md` – kontroluj, že je dodržuje.

## Role

1. **Analýza legacy** – zdrojem pravdy jsou soubory v `CICS/`, `COB-PROG/`, `DB2/`, `AS-400/`. Originál nelze spustit; každé tvrzení o chování musí být dohledatelné v kódu, mapě, DDL nebo snímku obrazovky. Kde se liší kód a snímek, uveď obojí.
2. **Návrh** – `docs/rewrite/02-functional-spec.md` (chování), `03-target-architecture.md` (stack, schéma, mapování), `04-migration-plan.md` (kroky pro Codex). Změny chování označuj jako *rekonstrukce* / *návrh* / *odchylka*.
3. **Review PR od Codexu** – viz checklist níže. Výsledek review piš do PR (GitHub review). Je-li PR v pořádku, **mergni ho squash-merge do `rewrite`** a smaž větev; pak napiš zadání dalšího kroku do `docs/rewrite/codex-tasks/<ID>.md` a jeho text předej uživateli (ten ho zadává do Codex Cloud). Rozhodnutí s dopadem na specifikaci promítni do `docs/rewrite/`.
5. **Zadání pro Codex** – každý krok plánu má samostatný, 1:1 vložitelný brief v `docs/rewrite/codex-tasks/<ID>.md`: kontext (které dokumenty jsou závazné), přesný rozsah včetně konkrétních dat a názvů, akceptační kritéria, jak spustit testy, pravidla PR. Drž frontu alespoň jednoho kroku napřed.
4. **Údržba dokumentace** – `docs/rewrite/` je živá. Po každém merge zkontroluj, zda plán a inventář (kap. 6 „stav“) odpovídají realitě.

## Neměnná pravidla

- Cílová větev `rewrite`; nikdy nepushuj do `main`.
- Legacy adresáře a kořenový `README.md` se nemění.
- Nová aplikace je jen v `app/`; dokumentace přepisu jen v `docs/rewrite/`; pravidla v `AGENTS.md` / `CLAUDE.md`.
- Žádné soubory v `.github/workflows/` (CI se nepoužívá, kontroly běží lokálně přes `make check`).
- Vlastní změny dokumentace a zadání (`docs/rewrite/`, `AGENTS.md`, `CLAUDE.md`) commituj přímo do `rewrite` (schváleno uživatelem 2026-09-11). Cokoli v `app/` děláš přes PR.
- Dokumenty česky, názvy programů, map, tabulek a polí v originále (`SRCHFLY`, `FLIGHTNUM`, …), UI texty anglicky.
- Do commitů, kódu a PR nepiš identifikátory modelů AI.

## Checklist review PR od Codexu

Rozsah a proces:
- [ ] PR odpovídá právě jednomu kroku z `04-migration-plan.md`; závislosti kroku jsou mergnuté.
- [ ] Větev `codex/<ID>-<slug>`, cíl `rewrite`, popis podle šablony (ID kroku, výstup `make check`, odchylky, checklist).
- [ ] Nedotčeny legacy adresáře, žádné `.github/workflows/`, žádná tajemství, žádné CDN.
- [ ] Záznam v `docs/rewrite/CHANGELOG.md`.

Chování:
- [ ] Každé akceptační kritérium kroku je pokryto testem (dohledej test ke každému bodu).
- [ ] Hlášky a validace odpovídají `02-functional-spec.md` (kódy `E-…`, pořadí validací, limity délek).
- [ ] Oprávnění: každá nová URL má test na 403 pro cizí roli.
- [ ] Odchylky od specifikace jsou uvedeny v PR; rozhodni (přijmout → upravit spec, nebo vrátit).

Kód a data:
- [ ] Logika ve `services.py`, views tenké, `Decimal` pro peníze, `timezone.localdate()` pro „dnes“.
- [ ] Modely: `db_table`/`db_column` legacy názvy, constraints a indexy dle `03` kap. 4, migrace přiložené a nazvané.
- [ ] Transakce a zámky tam, kde spec vyžaduje (prodej: `select_for_update` na letu).
- [ ] Testy nezávisí na síti a aktuálním datu.
- [ ] `make check` je zelený i ve tvém prostředí, když je to proveditelné (spusť `cd app && make check`, nebo alespoň `ruff` a `pytest` bez Dockeru s `DATABASE_URL` na lokální PostgreSQL).

Výstup review: „Approve“ jen když je vše splněno; jinak „Request changes“ s konkrétními body odkazujícími na řádky a na kapitoly specifikace.

## Postup pro vlastní změny dokumentace

1. `git fetch origin rewrite && git checkout -b claude/<slug> origin/rewrite`
2. Uprav `docs/rewrite/*.md`; při změně chování aktualizuj i `04-migration-plan.md` (akceptační kritéria dotčených kroků) a `CHANGELOG.md`.
3. Commit, push, PR do `rewrite` s popisem, které kroky a proč se mění.

## Rychlá orientace v legacy

| Co hledáš | Kde |
|---|---|
| Přihlášení, role, hash hesla | `CICS/LOGIN/LOGIN-COB`, `CICS/LOGIN/CRYPTO-VERIFICATION`, `COB-PROG/EMPLO-INSERT/EMPLO-CRYPTO-PASS` |
| Hledání letů | `CICS/SALES-MAP/SRCHFLY-COB`, mapa `SRCHFLI-MAP`, snímky `SRCHFLY*.png` |
| Hledání letenek, tisk | `CICS/SALES-MAP/SRCHTKT-COB`, `SRCHTKT-MAP`, `PRINT-TICKET-COB`, `TICKET-FORMAT` |
| Prodej | `CICS/SALES-MAP/SELL1-COB`, `SELL1-MAP`, `SELL2-MAP` (program `SELLCOB2` chybí), snímky `sell*.png`, `RECEIPT-COB` |
| Schéma | `DB2/create-db`, `DB2/DCLGEN/*`, `DB2/DER-COB-AIRLINES.pdf` |
| Testovací data | `DB2/insertion-*`, `COB-PROG/EMPLO-INSERT/EMPLOYEE-LIST.json`, `COB-PROG/PASSENGER-INSERT/*.xml` |
| Generování letů | `COB-PROG/FLIGHT-DUPLICATE/FLIGHT-DUPLICATE-COB` |

Podrobný inventář: `docs/rewrite/01-inventory.md`.
