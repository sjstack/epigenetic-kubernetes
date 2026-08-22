"""Deterministic characterization of the frozen legacy controller."""

from __future__ import annotations

import os

import pytest
from controller.clock import FakeClock
from controller.mocks.k8s_client import mock_db


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("MOCK_K8S", "true")
    monkeypatch.setenv("NAMESPACE", "epigenetik")
    monkeypatch.setenv("STRESS_THRESHOLD", "1")
    monkeypatch.setenv("STABILITY_WINDOW", "10")


def _controller(strategy: str, clock: FakeClock):
    os.environ["ORGANISM_STRATEGY"] = strategy
    mock_db.reset()
    from controller.epigenetic_controller import EpigeneticController

    return EpigeneticController(clock=clock, sleeper=clock.sleep)


def _cycle(strategy: str) -> list[str]:
    clock = FakeClock(start=5_000.0)
    ctrl = _controller(strategy, clock)
    if strategy == "clonal":
        pod = mock_db.get_pod("clonal-organism-pod-1", "epigenetik")
        parent = "clonal-organism"
        getter = mock_db.get_deployment
    else:
        pod = mock_db.get_pod("organism-0-0", "epigenetik")
        parent = "organism-0"
        getter = mock_db.get_statefulset

    assert pod is not None
    ctrl.handle_stress_event(pod)
    obj = getter(parent, "epigenetik")
    assert obj.spec.template.metadata.annotations["epigenetic-mark.science/methylation-level"] == "1"

    clock.advance(ctrl.stability_window + 0.5)
    ctrl.check_pods_stability()
    obj = getter(parent, "epigenetik")
    assert obj.spec.template.metadata.annotations["epigenetic-mark.science/methylation-level"] == "0"
    return list(ctrl.transition_log)


def test_clonal_characterization_is_repeatable(mock_env):
    first = _cycle("clonal")
    second = _cycle("clonal")
    assert first == second
    assert any("Methylating to level 1" in line for line in first)
    assert any("Demethylating to level 0" in line for line in first)


def test_lineage_characterization_is_repeatable(mock_env):
    first = _cycle("transgenerational")
    second = _cycle("transgenerational")
    assert first == second
    assert any("Lineage member organism-0 died" in line for line in first)
