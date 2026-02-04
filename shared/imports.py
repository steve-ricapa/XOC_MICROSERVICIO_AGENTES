"""Import helpers for shared libraries."""

from pathlib import Path
import sys


def ensure_repo_root_on_path() -> None:
    functions_root = Path(__file__).resolve().parents[2]
    functions_root_str = str(functions_root)
    if functions_root_str not in sys.path:
        sys.path.insert(0, functions_root_str)
