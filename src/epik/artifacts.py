from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from epik.canonical import canonical_dumps
from epik.engine.engine import Engine, dump_run


def save_run(path: str | Path, engine: Engine, extra: dict[str, Any] | None = None) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    world = engine.state.get("world") or {}
    (path / "digest.txt").write_text(engine.digest() + "\n")
    (path / "checkpoint.json").write_text(canonical_dumps(engine.checkpoint()))
    (path / "ledger.json").write_text(canonical_dumps(engine.ledger.to_list()))
    (path / "world.json").write_text(canonical_dumps(world))
    manifest = {
        "schema": "epik.artifact-manifest.v1",
        "digest": engine.digest(),
        "state_digest": engine.state_digest(),
        "event_digest": engine.event_digest(),
        "seed": engine.seed,
        "files": ["digest.txt", "checkpoint.json", "ledger.json", "world.json"],
        "extra": extra or {},
    }
    (path / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    (path / "run.json").write_text(canonical_dumps(dump_run(engine)))
    return path


def load_checkpoint(path: str | Path) -> Engine:
    path = Path(path)
    payload = json.loads((path / "checkpoint.json").read_text())
    return Engine.restore(payload)


def load_digest(path: str | Path) -> str:
    return Path(path).joinpath("digest.txt").read_text().strip()
