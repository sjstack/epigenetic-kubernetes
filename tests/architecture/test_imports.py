from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src" / "epik"


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_kernel_does_not_import_kubernetes_or_ports():
    forbidden = ("kubernetes", "epik.operator", "epik.api", "epik.integration", "epik.agents")
    for folder in ("engine", "model", "mechanisms"):
        for path in (ROOT / folder).rglob("*.py"):
            for name in _imports(path):
                assert not any(name == f or name.startswith(f + ".") for f in forbidden), (path, name)


def test_adapter_does_not_import_engine_or_mechanisms():
    path = ROOT / "integration" / "adapter.py"
    for name in _imports(path):
        assert not name.startswith("epik.engine")
        assert not name.startswith("epik.mechanisms")
