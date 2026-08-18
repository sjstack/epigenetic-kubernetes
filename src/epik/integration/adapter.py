"""Out-of-process PhenotypeAdapter: maps model outputs onto a sample app config.

This module must not import the engine, reducer, or mechanisms.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _dig(data: dict, path: str, default=None):
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def adapt_world(world: dict, target_attribute: str = "spec.replicas") -> dict:
    size = float(_dig(world, "phenotype.seed_size", 1.0) or 1.0)
    viability = float(_dig(world, "phenotype.viability", 1.0) or 1.0)
    replicas = max(1, int(round(3 * size * viability)))
    return {
        "schema": "epik.phenotype-adapter.v1",
        "target_attribute": target_attribute,
        "value": replicas,
        "source": "phenotype.seed_size",
        "notes": "Demo only. Does not write engine state.",
        "sample_app": {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "sample-processor"},
            "spec": {"replicas": replicas if target_attribute == "spec.replicas" else 1},
        },
    }


def adapt_artifact(world_path: str | Path, out_path: str | Path | None = None, target_attribute: str = "spec.replicas") -> dict:
    world = json.loads(Path(world_path).read_text())
    if "phenotype" not in world and "world" in world:
        world = world["world"]
    config = adapt_world(world, target_attribute=target_attribute)
    if out_path:
        Path(out_path).write_text(json.dumps(config, indent=2, sort_keys=True))
    return config
