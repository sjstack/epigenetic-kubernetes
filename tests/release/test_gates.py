from __future__ import annotations

from pathlib import Path

from epik.release.gates import run_release_gates


def test_release_gates_pass():
    report = run_release_gates(seed=1)
    assert report["passed"], report["failed"]


def test_dockerfile_is_hardened():
    text = Path("deploy/docker/Dockerfile").read_text()
    assert "USER 65532" in text
    assert "3.11" in text
    compose = Path("deploy/docker/docker-compose.yaml").read_text()
    assert "65532" in compose


def test_chaos_is_infrastructure_only():
    text = Path("tests/resilience/chaos-pod-kill.yaml").read_text()
    assert "pod-kill" in text
    assert "epik-run" in text
    archived = Path("manifests/chaos-experiment.yaml").read_text()
    assert "biologically inert" in archived.lower() or "Infrastructure" in archived
