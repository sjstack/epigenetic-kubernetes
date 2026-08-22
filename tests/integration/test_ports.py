from __future__ import annotations

import json
from pathlib import Path

import pytest

from epik.canonical import canonical_dumps
from epik.integration.adapter import adapt_artifact
from epik.integration.tape import ExposureTapeError, transcribe_telemetry, validate_tape
from epik.simulate import run_cross


def test_tape_rejects_undeclared_type():
    with pytest.raises(ExposureTapeError):
        validate_tape({"schema": "epik.exposure-tape.v1", "exposures": [{"type": "cpu_scale", "dap": 3}]})


def test_live_tape_replays_identically():
    samples = [
        {"metric": "cluster_cpu_heat", "dap": 3, "t": 3, "magnitude": 1.0},
        {"metric": "unknown_metric", "dap": 3, "t": 3, "magnitude": 9.0},
    ]
    live = transcribe_telemetry(samples)
    offline = transcribe_telemetry(json.loads(canonical_dumps(samples)))
    assert canonical_dumps(live) == canonical_dumps(offline)
    e1, w1 = run_cross("Col-0", "Cvi", seed=9, to_dap=3, exposure_tape=live)
    e2, w2 = run_cross("Col-0", "Cvi", seed=9, to_dap=3, exposure_tape=offline)
    assert e1.digest() == e2.digest()
    assert w1["pathways"]["DRM2"]["rate"] < 0.72


def test_adapter_maps_without_engine_write(tmp_path):
    _, world = run_cross("Col-0", "Ler", seed=1, to_dap=3)
    world_path = tmp_path / "world.json"
    world_path.write_text(json.dumps(world))
    cfg = adapt_artifact(world_path, out_path=tmp_path / "app.json", target_attribute="spec.replicas")
    assert cfg["target_attribute"] == "spec.replicas"
    assert cfg["sample_app"]["spec"]["replicas"] >= 1
    source = Path(__import__("epik.integration.adapter", fromlist=["x"]).__file__).read_text()
    assert "epik.engine" not in source
    assert "epik.mechanisms" not in source
