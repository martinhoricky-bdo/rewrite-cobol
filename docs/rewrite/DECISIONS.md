# Rozhodnutí přijatá během přepisu

Záznam rozhodnutí, která Claude přijal v automatickém režimu bez dotazu na uživatele (nejnovější nahoře). Formát: datum, kontext, rozhodnutí, dopad.

## 2026-09-11 – PR za Codex, když `gh` selže
- Kontext: smoke test – Codex větev pushnul, ale PR neotevřel (`gh` v sandboxu nepřihlášené).
- Rozhodnutí: Claude PR otevře sám z pushnuté větve; do zadání se přidává věta o fallbacku „branch pushed: <větev>“ (viz `AGENTS.md` kap. 0).
- Dopad: žádný na kód; proces v `AGENTS.md`, `CLAUDE.md`.

## 2026-09-11 – Konvence issue/labelů
- Kontext: uživatel odkazoval na konvence z jiných projektů (soc2, clientportal), které nejsou v této session dostupné.
- Rozhodnutí: použity vlastní labely `codex-task`, `step:R<ID>`, `smoke-test`, `needs-review`, `changes-requested`, `approved`; komentář se zmínkou `@codex` má pevný text (`CLAUDE.md`).
- Dopad: sjednotit později, pokud uživatel dodá původní konvence.
