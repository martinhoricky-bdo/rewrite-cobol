# STATUS – stav přepisu

Aktualizuje Claude po každé kontrole. Časy UTC.

## Souhrn
- Poslední aktualizace: 2026-09-11 21:14
- Aktuální krok: R04 (Codex pracuje)
- Blokuje: nic

## Hotovo
| Krok | Issue | PR | Merge |
|---|---|---|---|
| R00 analýza a dokumentace | – | #1 | 2026-09-11 18:41 |
| Smoke test Codex Cloud | #2 | #3 | 2026-09-11 19:33 (PR otevřel Claude, Codex větev pushnul; `gh` v sandboxu nebylo přihlášené, cache resetována) |
| R01 scaffolding | #4 | #5 | 2026-09-11 20:05 (1. běh selhal na push 403 kvůli tokenu; 2. běh OK, review čisté, 6 testů) |
| R02 datové schéma | #6 | #7 | 2026-09-11 20:25 (review čisté, 39 testů, schéma ověřeno v PostgreSQL) |
| R03 seed_demo | #8 | #9 | 2026-09-11 21:10 (1. běh push 403; 2. běh bez PostgreSQL – vráceno: bug `--from-date`, chybějící testy; oprava OK: 43 testů, seed 641/720/360, idempotentní) |

## Běží
| Krok | Issue | PR | Stav |
|---|---|---|---|
| R04 auth + role + navigace | #10 | – | zadáno 21:14, čeká se na PR |

## Fronta
R05 → R06 → R07 → R08 → R09 → R10 → R11 → R12 → R13 → R14 → R15 → R16a → R16b → R17 → R18 (zadání v `codex-tasks/`)

## Poznámky
- Vzdálená větev `claude/00-analysis-docs` zůstala na GitHubu (mazání větví přes git proxy neprochází) – neškodí, smazat ručně.
- Codex sandbox: po resetu cache má fungovat `gh`; fallback „branch pushed“ platí dál.
- Push 403 se opakuje nepravidelně (R01/1, R03/1 selhaly; R01/2, R02 prošly) – vypadá to na cache kontejneru bez tokenu. Pokud se to bude opakovat, je potřeba zásah uživatele v nastavení Codex Cloud prostředí.
