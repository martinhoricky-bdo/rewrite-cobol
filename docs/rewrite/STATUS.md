# STATUS – stav přepisu

Aktualizuje Claude po každé kontrole. Časy UTC.

## Souhrn
- Poslední aktualizace: 2026-09-11 20:08
- Aktuální krok: R02 (zadávání)
- Blokuje: nic

## Hotovo
| Krok | Issue | PR | Merge |
|---|---|---|---|
| R00 analýza a dokumentace | – | #1 | 2026-09-11 18:41 |
| Smoke test Codex Cloud | #2 | #3 | 2026-09-11 19:33 (PR otevřel Claude, Codex větev pushnul; `gh` v sandboxu nebylo přihlášené, cache resetována) |
| R01 scaffolding | #4 | #5 | 2026-09-11 20:05 (1. běh selhal na push 403 kvůli tokenu; 2. běh OK, review čisté, 6 testů) |

## Běží
| Krok | Issue | PR | Stav |
|---|---|---|---|

## Fronta
R03 → R04 → R05 → R06 → R07 → R08 → R09 → R10 → R11 → R12 → R13 → R14 → R15 → R16a → R16b → R17 → R18 (zadání v `codex-tasks/`)

## Poznámky
- Vzdálená větev `claude/00-analysis-docs` zůstala na GitHubu (mazání větví přes git proxy neprochází) – neškodí, smazat ručně.
- Codex sandbox: po resetu cache má fungovat `gh`; fallback „branch pushed“ platí dál.
