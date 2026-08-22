from __future__ import annotations

from epik.engine.engine import Engine
from epik.engine.intents import Intent


def ensure_flippers(engine: Engine, n: int = 4) -> None:
    for i in range(n):
        eid = f"flipper-{i}"
        engine.state.setdefault("entities", {}).setdefault(eid, {"kind": "flipper", "value": 0})


def toy_step(engine: Engine, n_entities: int = 4, p: float = 0.35) -> None:
    ensure_flippers(engine, n_entities)
    t = engine.clock.t
    for i in range(n_entities):
        eid = f"flipper-{i}"
        rng = engine.rng.stream("toy", "propose", eid, t)
        if rng.random() < p:
            engine.propose(
                Intent(
                    kind="flip",
                    mechanism="toy",
                    entity_id=eid,
                    payload={},
                    logical_time=t,
                )
            )
    engine.commit_pending()


def run_toy(seed: int, steps: int, n_entities: int = 4) -> Engine:
    engine = Engine(seed=seed)
    ensure_flippers(engine, n_entities)
    for _ in range(steps):
        toy_step(engine, n_entities=n_entities)
    return engine
