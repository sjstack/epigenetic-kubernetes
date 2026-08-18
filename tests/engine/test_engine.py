from __future__ import annotations

import random
from pathlib import Path

from epik.engine.engine import Engine
from epik.engine.intents import Intent
from epik.engine.toy import run_toy, toy_step


def test_identical_seed_identical_digest():
    a = run_toy(7, 12)
    b = run_toy(7, 12)
    assert a.digest() == b.digest()
    assert a.state_digest() == b.state_digest()
    assert a.event_digest() == b.event_digest()


def test_shuffled_intent_delivery():
    engine = Engine(seed=3)
    t = engine.clock.t
    intents = [
        Intent(kind="flip", mechanism="toy", entity_id=f"flipper-{i}", payload={}, logical_time=t)
        for i in range(6)
    ]
    e1 = Engine(seed=3)
    for intent in intents:
        e1.propose(intent)
    e1.commit_pending()

    e2 = Engine(seed=3)
    shuffled = list(intents)
    random.Random(123).shuffle(shuffled)
    for intent in shuffled:
        e2.propose(intent)
    e2.commit_pending()
    assert e1.digest() == e2.digest()


def test_checkpoint_resume_matches_full_run():
    full = run_toy(11, 10)
    mid = run_toy(11, 5)
    restored = Engine.restore(mid.checkpoint())
    for _ in range(5):
        toy_step(restored, n_entities=4)
    assert restored.digest() == full.digest()


def test_engine_has_no_kubernetes_import():
    import epik.engine.engine as mod

    source = Path(mod.__file__).read_text()
    assert "kubernetes" not in source
