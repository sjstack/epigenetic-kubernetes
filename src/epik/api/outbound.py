from __future__ import annotations

from typing import Any

from epik.engine.engine import Engine
from epik.engine.intents import Event


class OutboundAPI:
    """Read-only view of a run. Callers must not mutate engine state."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def digest(self) -> str:
        return self._engine.digest()

    def export(self) -> dict[str, Any]:
        return {
            "schema": "epik.export.v1",
            "digest": self._engine.digest(),
            "state_digest": self._engine.state_digest(),
            "event_digest": self._engine.event_digest(),
            "seed": self._engine.seed,
            "events": self._engine.ledger.to_list(),
            "world": self._engine.state.get("world"),
        }

    def follow(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._engine.ledger.events]

    def query(self, *, kind: str | None = None, mechanism: str | None = None) -> list[dict[str, Any]]:
        rows = self.follow()
        if kind:
            rows = [r for r in rows if r["kind"] == kind]
        if mechanism:
            rows = [r for r in rows if r["mechanism"] == mechanism]
        return rows


def attach_consumer(engine: Engine, sink: list[Event]) -> None:
    engine.subscribe(lambda event: sink.append(event))


def seed_dashboard(world: dict) -> dict[str, Any]:
    """Demo consumer: seed-development report from model output only."""
    pheno = world.get("phenotype") or {}
    calls = (world.get("imprinting_calls") or {}).get("endosperm") or {}
    highlights = {
        loc: {"call": info.get("call"), "maternal_fraction": info.get("maternal_fraction")}
        for loc, info in calls.items()
        if loc in {"MEA", "FWA", "FIS2", "PHE1", "HDG3", "ACT7"}
    }
    return {
        "schema": "epik.consumer.seed-dashboard.v1",
        "cross": world.get("cross_id"),
        "dap": world.get("dap"),
        "phenotype": pheno,
        "imprinting": highlights,
        "read_only": True,
    }
