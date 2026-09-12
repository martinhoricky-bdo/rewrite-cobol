# STATUS – stav přepisu

Aktualizuje Claude po každé kontrole. Časy UTC.

## Souhrn
- Poslední aktualizace: 2026-09-12 06:20
- Fáze 1 (R00–R18): hotovo. **Fáze 2 – refaktoring na idiomatické Django (R19–R22)**: běží, zadáno uživatelem 2026-09-12 („není DRY, žádné generic views“).
- Aktuální krok: R19 (Codex pracuje)
- Blokuje: nic

## Hotovo
| Krok | Issue | PR | Merge |
|---|---|---|---|
| R00 analýza a dokumentace | – | #1 | 2026-09-11 18:41 |
| Smoke test Codex Cloud | #2 | #3 | 2026-09-11 19:33 (PR otevřel Claude, Codex větev pushnul; `gh` v sandboxu nebylo přihlášené, cache resetována) |
| R01 scaffolding | #4 | #5 | 2026-09-11 20:05 (1. běh selhal na push 403 kvůli tokenu; 2. běh OK, review čisté, 6 testů) |
| R02 datové schéma | #6 | #7 | 2026-09-11 20:25 (review čisté, 39 testů, schéma ověřeno v PostgreSQL) |
| R03 seed_demo | #8 | #9 | 2026-09-11 21:10 (1. běh push 403; 2. běh bez PostgreSQL – vráceno: bug `--from-date`, chybějící testy; oprava OK: 43 testů, seed 641/720/360, idempotentní) |
| R04 auth + role + navigace | #10 | #11 | 2026-09-11 21:28 (review čisté, 64 testů, ruční průchod všech rolí) |
| R05 hledání letů | #12 | #13 | 2026-09-11 21:48 (review čisté, 86 testů, ruční průchod obrazovky) |
| R06 hledání letenek + detail | #14 | #15 | 2026-09-11 22:23 (1. běh push 403; 2. běh OK, review čisté, 115 testů) |
| R07 palubní vstupenka | #16 | #17 | 2026-09-11 22:56 (1. běh bez pushe – proxy 502; 2. běh OK, review čisté, 124 testů, ruční průchod tisku a oprávnění) |
| R08 cestující | #18 | #19 | 2026-09-11 23:18 (1. běh OK, review čisté, 159 testů, ruční průchod seznamu/detailu/formuláře a oprávnění) |
| R09 prodej krok 1 | #20 | #21 | 2026-09-11 23:45 (1. běh OK, 178 testů, ruční průchod rekapitulace/hlášek/oprávnění; Claude opravil ve větvi izolaci testů – `DepartmentFactory` get_or_create) |
| R10 prodej krok 2 + potvrzení | #22 | #23 | 2026-09-12 00:08 (1. běh OK, 196 testů vč. souběhu na PostgreSQL, ruční prodej 641+100+200 → CB00000002..4/A01..C01/362.97; Claude doplnil test 403 pro `buy_detail`, číslo PR v CHANGELOG a nezávislost testu ID na sekvenci) |
| R11 účtenka + hromadný tisk | #24 | #25 | 2026-09-12 00:27 (1. běh OK, 208 testů, ruční průchod účtenky dle RECEIPT-FORMAT a 3 vstupenek; Claude doplnil číslo PR v CHANGELOG) |
| R12 e2e testy Sales (Playwright) | #26 | #27 | 2026-09-12 00:55 (1. běh OK; Codex e2e nemohl spustit – sandbox blokuje stažení Chromia; Claude testy rozběhl lokálně: scope fixtur, `role="button"` lokátory, navigace na účtenku, `.first` u duplicitních textů → 9/9 dvakrát bez flush; 206 unit/view testů) |
| R13 IT Support (účty, letiště, letadla) | #28 | #29 | 2026-09-12 01:24 (1. běh OK; review 1: chování správné, vráceno kvůli chybějícím testům ze zadání §5; fix run doplnil testy za 6 min; 226 testů, ruční průchod reset hesla → /password/, deaktivace, CRUD, E-REF-01, oprávnění) |
| R14 import z exportu DB2 | #30 | #31 | 2026-09-12 01:50 (1. běh skončil prázdně; 2. běh OK, 231 testů, dry-run na fixtures dle AK 1, pořadí sloupců ověřeno proti DDL; Claude opravil umístění a číslo záznamu v CHANGELOG) |
| R15 HR – zaměstnanci a oddělení | #32 | #33 | 2026-09-12 02:11 (1. běh OK, 244 testů, ruční průchod: 10000040 založen → IT reset → /password/, oddělení 7 manažer 10000019, CEO read-only; Claude opravil pád seznamu na nečíselný filtr `?dept=abc`) |
| R16a Schedule – lety a generování | #34 | #35 | 2026-09-12 02:31 (1. běh OK, 258 testů, ruční průchod: generování CB2204 7/0 mimo seed a 0/7 v seedu, CRUD letů, E-REF-01, 403; seed po přesunu generátoru idempotentní; bez oprav) |
| R16b Schedule – posádky a směny | #36 | #37 | 2026-09-12 02:49 (1. běh OK, 274 testů, ruční průchod: posádka 13 z oddělení 2/3/4, směna na zítřek, překryv/obrácené časy odmítnuty, E-REF-01, 403; Claude doplnil číslo PR v CHANGELOG) |
| R17 Crew my shifts + CEO dashboard | #38 | #39 | 2026-09-12 03:04 (1. běh OK, 297 testů, ruční průchod: 10000003 → /crew/my-shifts/ s CB2204/CB2205, `past=1`, jiný člen posádky směny nevidí; CEO dashboard karty + 3 tabulky nad e2e prodeji, neplatné filtry 200, agregace v ORM (9 dotazů); 403 pro ostatní role; bez oprav) |
| R18 Hardening a závěr | #40 | #41 | 2026-09-12 05:38 (1. běh OK, 310 testů, e2e 9/9 dvakrát proti runserveru; ruční průchod: limiter 10/15 min per USERID+IP, `check --deploy` s `.env.example` bez varování, collectstatic s whitenoise, 404/403, placeholder jen legal, menu vs. matice; Claude opravil: 500 handler bez request kontextu + test, `SECRET_KEY` jen v build kroku Dockerfile, `hr*`/`reports*` ve wheelu, poznámka o per-proces limiteru v README) |

## Běží
| Krok | Issue | PR | Stav |
|---|---|---|---|
| R19 Základ refaktoringu: generické views, mixiny, šablony, fleet | – | – | zadávání |

## Fronta
R20 (schedule/HR/IT), R21 (sales/reports) – po R19, mohou běžet po sobě; R22 (úklid, matice oprávnění, docs) – po R20 a R21. Zadání v `codex-tasks/R20–R22.md`.

## Co zbývá ručně (uživatel)
- Smazat vzdálené větve `claude/00-analysis-docs` a `codex/*` (mazání přes git proxy z prostředí Claude neprochází; všechny jsou mergnuté).
- Nasazení: sestavit image (`docker build`), nastavit reálný `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL` (viz `app/README.md`), spustit `migrate` a `import_legacy` z exportu DB2.
- Rozhodnout otevřené body z `02-functional-spec.md` (platební metoda u účtenky, role legal bez funkcí).
- Codex Cloud: nepravidelné selhání pushe na 1. běhu (viz poznámky) – zkontrolovat token v nastavení prostředí, pokud se bude Codex používat dál.

## Poznámky
- Vzdálená větev `claude/00-analysis-docs` zůstala na GitHubu (mazání větví přes git proxy neprochází) – neškodí, smazat ručně.
- Codex sandbox: po resetu cache má fungovat `gh`; fallback „branch pushed“ platí dál.
- Codex sandbox nemá Docker ani Chromium (`playwright install` → 403 „Domain forbidden“). E2E testy (R12, případně další) ověřuje Claude lokálně proti `runserver` s předinstalovaným Chromiem; Codex je odevzdává „naslepo“, drobné opravy lokátorů dělá Claude přímo ve větvi.
- Dev DB (`airlines`) obsahuje po e2e bězích prodeje 641+100 na `CB1104` (19. 9., 13. 9., 14. 9., 15. 9.) a e2e cestující `E2E-<timestamp>`; seed je nemaže. Pro čistý stav `seed_demo --flush`.
- Push selhává nepravidelně na prvním běhu (R01/1, R03/1, R06/1 = 403; R07/1 = proxy 502; R08/1–R13/1 prošly; R14/1 skončil za minutu prázdným komentářem bez větve, R14/2 OK; R15/1, R16a/1 a R16b/1 OK; druhé běhy vždy prošly) – vypadá to na cache kontejneru bez tokenu. Pokud se to bude opakovat, je potřeba zásah uživatele v nastavení Codex Cloud prostředí.
