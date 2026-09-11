# Rozhodnutí přijatá během přepisu

Záznam rozhodnutí, která Claude přijal v automatickém režimu bez dotazu na uživatele (nejnovější nahoře). Formát: datum, kontext, rozhodnutí, dopad.

## 2026-09-11 – Opravy PR se zadávají zmínkou na issue, ne na PR
- Kontext: zmínka `@codex` v komentáři PR #9 spustila jen „Code Review“ (Codex na PR reaguje jako reviewer), ne opravný Cloud task.
- Rozhodnutí: požadavky na opravu se zadávají komentářem `@codex fix run …` na issue kroku s pokynem pushovat do stejné větve; review text zůstává na PR.
- Dopad: `CLAUDE.md` bod 5.

## 2026-09-11 – Review bez formálního Approve
- Kontext: Codex otevírá PR tokenem uživatele, takže GitHub odmítá „Approve“ vlastního PR.
- Rozhodnutí: review se zapisuje jako review typu COMMENT s hlavičkou „schváleno“, label `approved` a merge dělá Claude.
- Dopad: proces v `CLAUDE.md` bod 5 (formální Approve není podmínkou).

## 2026-09-11 – PR za Codex, když `gh` selže
- Kontext: smoke test – Codex větev pushnul, ale PR neotevřel (`gh` v sandboxu nepřihlášené).
- Rozhodnutí: Claude PR otevře sám z pushnuté větve; do zadání se přidává věta o fallbacku „branch pushed: <větev>“ (viz `AGENTS.md` kap. 0).
- Dopad: žádný na kód; proces v `AGENTS.md`, `CLAUDE.md`.

## 2026-09-11 – Konvence issue/labelů
- Kontext: uživatel odkazoval na konvence z jiných projektů (soc2, clientportal), které nejsou v této session dostupné.
- Rozhodnutí: použity vlastní labely `codex-task`, `step:R<ID>`, `smoke-test`, `needs-review`, `changes-requested`, `approved`; komentář se zmínkou `@codex` má pevný text (`CLAUDE.md`).
- Dopad: sjednotit později, pokud uživatel dodá původní konvence.
