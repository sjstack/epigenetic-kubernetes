#!/usr/bin/env python3
"""Deterministic mock-mode demo of the frozen legacy CPU-analogy controller."""

from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

os.environ["MOCK_K8S"] = "true"
os.environ["NAMESPACE"] = "epigenetik"
os.environ["STRESS_THRESHOLD"] = "1"
os.environ["STABILITY_WINDOW"] = "10"


def _run_strategy(strategy: str) -> list[str]:
    os.environ["ORGANISM_STRATEGY"] = strategy
    from controller.clock import FakeClock
    from controller.epigenetic_controller import EpigeneticController
    from controller.mocks.k8s_client import mock_db

    mock_db.reset()
    clock = FakeClock(start=1000.0)
    ctrl = EpigeneticController(clock=clock, sleeper=clock.sleep)

    if strategy == "clonal":
        pod = mock_db.get_pod("clonal-organism-pod-1", "epigenetik")
        name = "clonal-organism"
    else:
        pod = mock_db.get_pod("organism-0-0", "epigenetik")
        name = "organism-0"

    ctrl.handle_stress_event(pod)
    clock.advance(ctrl.stability_window + 1)
    ctrl.check_pods_stability()
    print(f"[{strategy}] transitions: {len(ctrl.transition_log)} last_event={ctrl.last_event_time.get(name)}")
    return list(ctrl.transition_log)


def main() -> int:
    clonal_a = _run_strategy("clonal")
    clonal_b = _run_strategy("clonal")
    lineage_a = _run_strategy("transgenerational")
    lineage_b = _run_strategy("transgenerational")
    if clonal_a != clonal_b or lineage_a != lineage_b:
        print("ERROR: legacy demo is not deterministic")
        return 1
    print("legacy-demo: clonal and transgenerational cycles are deterministic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
