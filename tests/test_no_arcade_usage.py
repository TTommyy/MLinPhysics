"""``physics_sim`` package must not depend on ``arcade``"""

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent / "physics_sim"


def _arcade_imports(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "arcade" or alias.name.startswith("arcade."):
                    hits.append(f"line {node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "arcade" or module.startswith("arcade."):
                imported = ", ".join(a.name for a in node.names)
                hits.append(f"line {node.lineno}: from {module} import {imported}")
    return hits


def _python_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.rglob("*.py")
        if "__pycache__" not in p.parts and ".venv" not in p.parts
    )


@pytest.fixture(scope="module")
def offenders() -> list[tuple[Path, list[str]]]:
    found: list[tuple[Path, list[str]]] = []
    for path in _python_files(PACKAGE_ROOT):
        hits = _arcade_imports(path)
        if hits:
            found.append((path, hits))
    return found


def test_no_file_in_package_uses_arcade(
    offenders: list[tuple[Path, list[str]]],
) -> None:
    if not offenders:
        return
    lines = []
    for path, hits in offenders:
        rel = path.relative_to(PACKAGE_ROOT).as_posix()
        for hit in hits:
            lines.append(f"  - {rel}: {hit}")
    msg = "\n".join(lines)
    pytest.fail(msg)
