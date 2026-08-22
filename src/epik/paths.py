from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    env = os.environ.get("EPIK_ROOT")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("cannot locate repository root (expected pyproject.toml)")


def schemas_dir() -> Path:
    return repo_root() / "schemas"


def profiles_dir() -> Path:
    return repo_root() / "profiles"
