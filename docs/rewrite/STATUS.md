# STATUS – stav přepisu

Aktualizuje Claude po každé kontrole. Časy UTC.

## Souhrn
- Poslední aktualizace: 2026-09-12 01:52
- Aktuální krok: R15 (Codex pracuje)
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

## Běží
| Krok | Issue | PR | Stav |
|---|---|---|---|
| R15 HR – zaměstnanci a oddělení | #32 | – | zadáno 01:52, čeká se na PR |

## Fronta
R16a → R16b → R17 → R18 (zadání v `codex-tasks/`)

## Poznámky
- Vzdálená větev `claude/00-analysis-docs` zůstala na GitHubu (mazání větví přes git proxy neprochází) – neškodí, smazat ručně.
- Codex sandbox: po resetu cache má fungovat `gh`; fallback „branch pushed“ platí dál.
- Codex sandbox nemá Docker ani Chromium (`playwright install` → 403 „Domain forbidden“). E2E testy (R12, případně další) ověřuje Claude lokálně proti `runserver` s předinstalovaným Chromiem; Codex je odevzdává „naslepo“, drobné opravy lokátorů dělá Claude přímo ve větvi.
- Dev DB (`airlines`) obsahuje po e2e bězích prodeje 641+100 na `CB1104` (19. 9., 13. 9., 14. 9., 15. 9.) a e2e cestující `E2E-<timestamp>`; seed je nemaže. Pro čistý stav `seed_demo --flush`.
- Push selhává nepravidelně na prvním běhu (R01/1, R03/1, R06/1 = 403; R07/1 = proxy 502; R08/1–R13/1 prošly; R14/1 skončil za minutu prázdným komentářem bez větve, R14/2 OK; druhé běhy vždy prošly) – vypadá to na cache kontejneru bez tokenu. Pokud se to bude opakovat, je potřeba zásah uživatele v nastavení Codex Cloud prostředí.
