"""Enforce descriptive documentation and legacy traceability across application code."""

import ast
import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_FILES = {"__init__.py", "asgi.py", "manage.py", "wsgi.py"}
EXCLUDED_PARTS = {"migrations", "tests"}
# One-line generic accessors may be listed here if documenting them would add no rule or context.
EXEMPT_PUBLIC_CALLABLES: frozenset[str] = frozenset()


def production_modules() -> list[Path]:
    """Return Python modules in the R23 scope, excluding framework entry points and tests."""
    return [
        path
        for path in sorted(APP_ROOT.rglob("*.py"))
        if path.name not in EXCLUDED_FILES
        and not EXCLUDED_PARTS.intersection(path.relative_to(APP_ROOT).parts)
        and path.parent != APP_ROOT / "config" / "settings"
    ]


def qualified_nodes(tree: ast.Module):
    """Yield classes and public callables with stable nested qualified names."""

    def walk(body, parents=()):
        for node in body:
            if isinstance(node, ast.ClassDef):
                qualified_name = ".".join((*parents, node.name))
                yield node, qualified_name
                yield from walk(node.body, (*parents, node.name))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified_name = ".".join((*parents, node.name))
                if not node.name.startswith("_") and qualified_name not in EXEMPT_PUBLIC_CALLABLES:
                    yield node, qualified_name
                yield from walk(node.body, (*parents, node.name))

    yield from walk(tree.body)


def identifier_sentence(identifier: str) -> str:
    """Convert an identifier to the trivial sentence forbidden by the R23 specification."""
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", identifier).replace("_", " ")
    return f"{words.lower()}."


def assert_descriptive_docstring(docstring: str | None, location: str) -> None:
    """Assert that a docstring is complete, substantial, and not a split identifier."""
    assert docstring, f"Missing docstring: {location}"
    normalized = " ".join(docstring.split())
    assert len(normalized) >= 30, f"Docstring shorter than 30 characters: {location}"
    assert normalized.endswith("."), f"Docstring must end with a period: {location}"
    identifier = location.rsplit(".", maxsplit=1)[-1]
    assert normalized.lower() != identifier_sentence(identifier), (
        f"Docstring only repeats its identifier: {location}"
    )


def test_application_docstrings_are_descriptive():
    """Check every in-scope module, class, and public callable required by R23."""
    counts = {"modules": 0, "classes": 0, "callables": 0}
    for path in production_modules():
        relative_path = path.relative_to(APP_ROOT)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative_path))
        assert_descriptive_docstring(ast.get_docstring(tree), str(relative_path))
        counts["modules"] += 1
        for node, qualified_name in qualified_nodes(tree):
            location = f"{relative_path}:{qualified_name}"
            assert_descriptive_docstring(ast.get_docstring(node), location)
            key = "classes" if isinstance(node, ast.ClassDef) else "callables"
            counts[key] += 1

    assert counts == {"modules": 52, "classes": 164, "callables": 184}
