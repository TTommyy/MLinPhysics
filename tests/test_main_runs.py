"""``main.py`` must run."""

import subprocess
import sys
from pathlib import Path

import pytest

MAIN_PATH = Path(__file__).resolve().parent.parent / "app" / "main.py"

def test_main_runs_without_error() -> None:
    try:
        result = subprocess.run(
            [sys.executable, str(MAIN_PATH)],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
    except subprocess.TimeoutExpired:
        return 

    pytest.fail(
        f"main.py exited with rc={result.returncode}"
    )
