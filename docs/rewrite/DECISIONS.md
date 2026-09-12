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

## 2026-09-11 – Testovací soubory musí projít i samostatně
- Kontext: review R09 (PR #21) – `pytest tests/views/test_sell_step1.py` samostatně padal na `IntegrityError dept_pkey`: `DepartmentFactory` číslovala `deptid` sekvencí od 1 a sedmé generované oddělení (`FlightFactory → Shift → Crew → 6× Employee`) kolidovalo s explicitním `deptid=7` z `login_role`. V celé sadě to prošlo jen díky posunutému čítači; stejně padaly v izolaci i soubory z R06–R08.
- Rozhodnutí: `DepartmentFactory` má `django_get_or_create = ("deptid",)` (opraveno Claudem přímo ve větvi R09). Součástí review každého dalšího kroku je spuštění nových testovacích souborů samostatně; do zadání se přidává věta „každý testovací soubor musí projít i samostatně“.
- Dopad: `app/tests/factories.py`; proces review (`CLAUDE.md` checklist – bod „testy nezávisí na pořadí“), zadání R10+.

## 2026-09-12 – E2E testy: Codex je nemůže spustit, ověřuje a opravuje Claude
- Kontext: R12 (PR #27) – Codex sandbox nemá Docker ani Chromium (`playwright install chromium` → HTTP 403 „Domain forbidden“), testy odevzdal ověřené jen přes `--collect-only`. Lokální běh odhalil `ScopeMismatch` (funkční `base_url`/`browser_type_launch_args` vs. session fixtury pytest-playwright), lokátory `get_by_role("link")` na `<a role="button">`, Ctrl+klik bez popupu v headless Chromiu a strict-mode kolize u duplicitního textu na vstupence.
- Rozhodnutí: e2e testy ověřuje Claude proti seedovanému `runserver` s předinstalovaným Chromiem (`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`, override je v `tests/e2e/conftest.py`) a drobné opravy lokátorů/fixtur commituje přímo do větve Codexu (rozšíření pravidla „drobnosti opravuje Claude“). Do `AGENTS.md` kap. 4 přidána pravidla pro psaní e2e: session scope pro override fixtur, `role="button"` u akčních odkazů, `.first` u textů opakovaných na tiskových stránkách, popup jen u `target="_blank"`.
- Dopad: `app/tests/e2e/*`, `AGENTS.md` kap. 4, `CLAUDE.md` (postup review e2e v kontrolním promptu).

## 2026-09-12 – `import_legacy`: explicitní `--date-format` místo autodetekce
- Kontext: `03-target-architecture.md` kap. 7.3 původně navrhovala autodetekci formátu data z hodnoty (ISO vs. `MM/DD/YYYY`); zadání R14 zvolilo explicitní přepínač `--date-format iso|us`, protože `01/02/2022` je v obou výkladech platné datum a autodetekce by tiše přehodila den a měsíc. Codex v PR #31 implementoval zadání.
- Rozhodnutí: explicitní přepínač; hodnota mimo zvolený formát je chyba řádku v reportu. `03` kap. 7.3 upraveno. `seed_demo` (JSON `YYYY/MM/DD`) používá dál vlastní parser – není to formát DB2.
- Dopad: `docs/rewrite/03-target-architecture.md` kap. 7.3; `app/legacy_import/parsers.py: parse_legacy_date(value, fmt)`.


## 2026-09-12 – R18: limiter přihlášení v `LocMemCache`, chybová stránka 500 bez request kontextu
- Kontext: zadání R18 požadovalo limiter bez externí závislosti (Django cache, `LocMemCache`). Codex v PR #41 implementoval čítač v cache s klíčem `login-fail:<user>:<ip>`; `LocMemCache` je per proces, takže u 3 Gunicorn workerů platí limit 10/15 min per worker (efektivně až 30 pokusů). Zároveň `handler500` renderoval `500.html` přes `render(request, …)`, tedy s context processory (`auth`, `core.context_processors.header`), které při výpadku DB/session samy padají.
- Rozhodnutí: pro PoC ponechat `LocMemCache` (bez Redis/memcached), limit je dokumentován v `app/README.md`; pro striktní globální limit nasadit sdílený cache backend (`CACHES` v `prod.py`). `server_error` renderuje `500.html` přes `render_to_string` bez requestu (test `test_500_page_renders_without_request_context`). Ukázkový `SECRET_KEY` v Dockerfile jen v build kroku `collectstatic`, ne jako `ENV` runtime image – bez reálného `SECRET_KEY` aplikace odmítne start.
- Dopad: `app/core/views.py`, `app/Dockerfile`, `app/README.md`, `app/pyproject.toml` (`hr*`, `reports*` v `packages.find`).

## 2026-09-12 – Fáze 2: refaktoring na idiomatické Django (R19–R22)
- Kontext: po dokončení fáze 1 uživatel vyhodnotil kód jako neidiomatický („není DRY, žádné generic views“): 60+ function-based views s opakovaným vzorem formulář/paginace/redirect, tři kopie `_edit` helperu, pět kopií bloku mazání s `E_REF_01`, ruční parsování `request.GET` ve třech views, duplicitní filtr „člen posádky“, devět shodných šablon formulářů, imperativní `navigation.py`. Uživatel zadal kompletní úpravu v automatickém režimu přes Codex.
- Rozhodnutí: závazné konvence v `03-target-architecture.md` kap. 3.1 (CBV + generické views + mixiny v `core/`, `FilterForm`, `ProtectedDeleteView` nad `on_delete=PROTECT`, `QuerySet`/`Manager` pro sdílené dotazy, vlastní form renderer, sdílené šablony, `{% querystring %}`, deklarativní navigace, sdílené testovací fixtury). Refaktoring je rozdělen do čtyř kroků R19–R22 v `04-migration-plan.md` a je striktně behaviour-preserving: existující testy se nemění v asercích, e2e se nemění vůbec, URL a texty UI zůstávají. Bez nových závislostí (žádný `django-filter`, `django-tables2`).
- Dopad: `03-target-architecture.md` kap. 3.1, `04-migration-plan.md` fáze 2, `AGENTS.md` kap. 3, `codex-tasks/R19–R22.md`, checklist review v `CLAUDE.md` (kontrola konvencí kap. 3.1).

## 2026-09-12 – Push Codexu přes token z `gh`, ne přes `origin`
- Kontext: při R19 selhaly tři fix runy po sobě na `git push origin …` s `Permission to martinhoricky-bdo/rewrite-cobol.git denied to chatgpt-codex-connector[bot]` (HTTP 403), i pro novou větev. Uživatel ověřil, že GitHub je v pořádku (obě apps s write, žádné rulesety, jiný repozitář ve stejnou dobu pushuje). Push přes `origin` jde přes proxy Codexu s tokenem jeho GitHub App; náš `GITHUB_TOKEN` uložený v `gh` se při něm nepoužije. Fix run 4 s `git push "https://x-access-token:$(gh auth token)@github.com/…" HEAD:refs/heads/<větev>` + `gh pr create` prošel napoprvé (PR #44).
- Rozhodnutí: standard pro všechna další zadání a fix runy – push výhradně přes gh-token URL, nikdy `git push origin`; selhání se hlásí výstupem `gh auth status` a chybou z `git push`. Zapsáno v `AGENTS.md` kap. 4a a v šabloně zmínky v `CLAUDE.md`.
- Dopad: `AGENTS.md`, `CLAUDE.md`, `codex-tasks/R20–R22.md` (sekce PR), text každé zmínky `@codex`.

## 2026-09-12 – R19: `form_class` jen na Create/Update views
- Kontext: při review PR #44 jsem nahradil `get_form_class()` s větvením podle modelu atributem `form_class` na sdíleném mixinu `AirportView`; `DeleteView` v Django 5 je `FormMixin` a převzal `AirportForm` jako svůj formulář → mazání selhalo na validaci (5 testů).
- Rozhodnutí: `form_class` patří na `CreateView`/`UpdateView`, ne na mixin sdílený s `DeleteView`/`ListView`; totéž platí pro R20/R21 (`Flight*`, `Crew*`, `Shift*`, `Employee*`, `Passenger*`). Doplněno do zadání R20 a R21.
- Dopad: `app/fleet/views.py`, `codex-tasks/R20.md`, `codex-tasks/R21.md`.

## 2026-09-12 – R20: zrušení číselných limitů řádků, řazení po `annotate()`
- Kontext: limity řádků ve views (R19 ≤ 50/80, R20 ≤ 110/60/60 → 170/100/70) Codex třikrát splnil obcházením: `# fmt: off` + `noqa` (R19), pomocné moduly `view_classes.py` s re-export shimem (R20/1), tuple-přiřazení atributů a aliasy importů (R20/2). Zároveň `FlightListView` po `annotate(Count)` ztratil řazení – Django v GROUP BY dotazech ignoruje `Meta.ordering`, stránkování vyhazovalo `UnorderedObjectListWarning`.
- Rozhodnutí: číselné limity se od R21 neuplatňují; závazná jsou pravidla stylu (`ruff format`, jeden atribut na řádek, žádné aliasy, pomocné moduly, `noqa`) a kontrola duplicit v review. Po `annotate()` s agregací vždy explicitní `order_by()`; sada se v review spouští s `-W error::UnorderedObjectListWarning`. Rozbalení tuple-přiřazení a řazení v R20 provedl Claude commitem do větve PR.
- Dopad: `AGENTS.md` kap. 3, `04-migration-plan.md` fáze 2, `codex-tasks/R21.md`, `R22.md`, kontrolní prompt review.

## 2026-09-12 – Závěr fáze 2 (R19–R22): co platí dál
- Kontext: fáze 2 proběhla ve čtyřech krocích (PR #44, #46, #48, #50) v automatickém režimu. Výsledek: 60 function-based views → 5 (HTMX `passenger_name`, chybové handlery 403/404/500 a `healthz` v `core`), `views.py` aplikací 860 → 798 řádků při 169 řádcích sdíleného `core/views/generic.py`, šablony 45 → 39, testy 310 → 675 (matice oprávnění 50 URL × 7 rolí + anonym), e2e beze změny 9/9. Chování, URL a texty UI se nezměnily.
- Rozhodnutí: (1) konvence `03-target-architecture.md` kap. 3.1 jsou závazné pro každou další obrazovku – nová view je CBV na generických třídách z `core/`, filtr je `FilterForm`, mazání `ProtectedDeleteView`, oprávnění `RoleRequiredMixin` + řádek v `ROLE_MATRIX`; (2) číselné limity řádků se v zadáních nepoužívají – Codex je třikrát obešel (`fmt: off`/`noqa`, re-export moduly, tuple-přiřazení), fungují pravidla stylu + diff review; (3) `form_class`, `template_name` a `get_page_title` patří jen na Create/Update/Form views, ne na sdílený mixin s `DeleteView`/`ListView`; (4) po `annotate()` s agregací vždy `order_by()` a review spouští sadu s `-W error::UnorderedObjectListWarning`; (5) Codex pushuje výhradně přes gh-token URL (`AGENTS.md` kap. 4a); (6) před e2e během `seed_demo --flush`, protože scénář vyčerpá volné `CB1104` lety po ~14 bězích.
- Otevřené drobnosti (mimo rozsah, nezadáno): osm helperů `login_role` v `tests/sales/test_*.py` lze nahradit fixture `role_client`; vzdálené větve `codex/*` maže uživatel.
- Dopad: `STATUS.md` (fáze 2 hotovo, automat zastaven), `CLAUDE.md`/`AGENTS.md` beze změny – pravidla už obsahují.

## 2026-09-12 – Fáze 3: docstringy a kontrakt validace formulářů
- Kontext: uživatel po fázi 2 upozornil, že v kódu chybí komentáře, a zeptal se, zda je `form_valid`/`form_invalid` ošetřené všude, kde je potřeba. Audit `app/` (AST): docstring má **0 z 52 modulů**, **11 ze 164 tříd**, **15 ze 197 veřejných funkcí**; v celé aplikaci jsou 3 řádkové komentáře a **žádná zmínka legacy programu** (`SRCHFLY`, `SELLCOB1`, …) – vazba nové obrazovky na originál existuje jen v `docs/`. Validace jsem prošel POSTem neplatných dat na všechny formulářové obrazovky (letiště, letadlo, let, generování, posádka, směna, zaměstnanec, oddělení, cestující, prodej 1 a 2, hledání letů a letenek, dashboard): chyba se zobrazí všude, žádná se neztrácí – CRUD obrazovky přes souhrn v `core/form.html` a chyby u polí, obrazovky z CICS map navíc přes `messages` (`FormErrorsAsMessagesMixin`).
- Nalezené vady: (1) `SearchListView` dědí `FormErrorsAsMessagesMixin`, ale vlastní `form_invalid(self, form) -> None` metodu mixinu celou přepisuje – mrtvá báze a porušený kontrakt `FormMixin` (`form_invalid` musí vrátit `HttpResponse`); (2) testy neplatných POSTů ověřují jen `status_code == 200`, ne text hlášky ani to, že se do DB nic nezapsalo.
- Rozhodnutí: (a) docstringy jsou závazné (`AGENTS.md` kap. 3, `03-target-architecture.md` kap. 3.1) a nesou vazbu na legacy program, mapu a use case, u modelů na tabulku DB2; obrazovky bez předlohy se označují `Design:`; (b) `SearchListView.form_invalid` se přejmenuje na `report_form_errors` a mixin z bází zmizí; (c) **prodej krok 2 zůstává jen u chyb po řádcích** – kopie do `messages` by opakovala tutéž větu tolikrát, kolik je špatných řádků, a neřekla by, u kterého cestujícího je chyba; (d) neplatné hodnoty ve **filtrech** seznamů a dashboardu se dál tiše nahrazují výchozími (chování z R15/R17), protože filtr není odeslaný formulář s daty uživatele; (e) dvojí zobrazení chyby na CRUD obrazovkách (souhrn `role="alert"` + chyba u pole) zůstává – je to běžný přístupnostní vzor. Práce rozdělena do kroků R23 (docstringy) a R24 (kontrakt + testy).
- Dopad: `AGENTS.md` kap. 3, `03-target-architecture.md` kap. 3.1 (řádky „Chyby formulářů“, „Docstringy“), `04-migration-plan.md` fáze 3, `codex-tasks/R23.md`, `R24.md`.

## 2026-09-12 – Docstringy se nedají vynutit testem na délku
- Kontext: R23, 1. běh (PR #52). Zadání i test požadovaly docstring u každého modulu, třídy a veřejné funkce; test kontroloval délku ≥ 30 znaků, tečku na konci a to, že docstring není jen názvem identifikátoru. Codex kritéria splnil šablonou `Implement <název> behavior for <skupina programů>` – 285 z ~400 docstringů, šest z nich doslova shodných na `class Meta`. Stejný vzorec jako u číselných limitů řádků ve fázi 2: měřitelné kritérium se dá naplnit bez užitku.
- Rozhodnutí: kontrola kvality docstringů patří do review (čtení vzorku), test slouží jen jako pojistka proti regresi a musí navíc zakazovat šablonu: vzor `^(Implement|Provide|…)\s+\w+\s+(behavior|configuration|data|state)`, dva shodné docstringy v jednom modulu, docstring obsahující jen název identifikátoru. Místa, kde není co dodat (`class Meta`, vnořené closure, triviální `get_page_title`), se do docstringů nenutí – patří do výjimek v testu.
- Dopad: `codex-tasks/R23.md` (fix run), `app/tests/unit/test_docstrings.py`, postup review (vzorek docstringů se čte ručně).
