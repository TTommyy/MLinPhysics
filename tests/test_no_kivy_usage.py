"""`kivy` must be imported. it must not be imported in forbidden dirs"""

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent / "physics_sim"
FORBIDDEN_DIRS = ("core", "engines", "forces", "entities")


def _kivy_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "kivy" or alias.name.startswith("kivy."):
                    hits.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "kivy" or module.startswith("kivy."):
                imported = ", ".join(a.name for a in node.names)
                hits.append(f"line {node.lineno}: from {module} import {imported}")
    return hits


def _python_files(root: Path) -> list[Path]:
    skip = {"__pycache__", ".venv", ".git", ".pytest_cache"}
    return sorted(
        p
        for p in root.rglob("*.py")
        if not any(part in skip or part.endswith(".egg-info") for part in p.parts)
    )


@pytest.fixture(scope="module")
def kivy_imports_anywhere() -> list[tuple[Path, list[str]]]:
    found: list[tuple[Path, list[str]]] = []
    for path in _python_files(PACKAGE_ROOT):
        hits = _kivy_imports(path)
        if hits:
            found.append((path, hits))
    return found


@pytest.fixture(scope="module")
def kivy_offenders_core() -> list[tuple[Path, list[str]]]:
    found: list[tuple[Path, list[str]]] = []
    for sub in FORBIDDEN_DIRS:
        for path in _python_files(PACKAGE_ROOT / sub):
            hits = _kivy_imports(path)
            if hits:
                found.append((path, hits))
    return found


def test_kivy_is_imported_somewhere(
    kivy_imports_anywhere: list[tuple[Path, list[str]]],
) -> None:
    if kivy_imports_anywhere:
        return
    pytest.fail("kivy is never imported anywhere in the repo")


def test_kivy_not_imported_in_forbidden_dirs(
    kivy_offenders_core: list[tuple[Path, list[str]]],
) -> None:
    if not kivy_offenders_core:
        return
    pytest.fail("kivy is imported in a forbidden dir ")
