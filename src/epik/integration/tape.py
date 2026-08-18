"""Inbound ExposureTape: declared environmental inputs only."""

from __future__ import annotations

from typing import Any

DECLARED_EXPOSURES: dict[str, dict[str, Any]] = {
    "heat_pulse": {"pathway": "DRM2", "op": "multiply_rate", "factor": 0.6},
    "drought": {"pathway": "MET1", "op": "multiply_rate", "factor": 0.9},
    "pathogen": {"pathway": "ROS1", "op": "multiply_rate", "factor": 1.3},
    "high_light": {"pathway": "DME", "op": "multiply_rate", "factor": 0.85},
    "nutrient_n": {"pathway": "CMT2", "op": "multiply_rate", "factor": 1.2},
}

SCHEMA = "epik.exposure-tape.v1"


class ExposureTapeError(ValueError):
    pass


def validate_tape(tape: dict) -> dict:
    if tape.get("schema") != SCHEMA:
        raise ExposureTapeError(f"schema must be {SCHEMA}")
    exposures = tape.get("exposures")
    if not isinstance(exposures, list):
        raise ExposureTapeError("exposures must be a list")
    cleaned = []
    for event in exposures:
        etype = event.get("type")
        if etype not in DECLARED_EXPOSURES:
            raise ExposureTapeError(f"undeclared exposure type {etype!r}")
        if "t" not in event and "dap" not in event:
            raise ExposureTapeError("exposure needs t or dap")
        cleaned.append(
            {
                "type": etype,
                "t": event.get("t"),
                "dap": event.get("dap"),
                "magnitude": float(event.get("magnitude", 1.0)),
                "target": event.get("target") or {},
            }
        )
    return {"schema": SCHEMA, "exposures": cleaned}


def record_tape(events: list[dict], metadata: dict | None = None) -> dict:
    tape = {"schema": SCHEMA, "metadata": metadata or {}, "exposures": events}
    return validate_tape(tape)


def apply_exposure(world: dict, etype: str, magnitude: float, target: dict) -> None:
    if etype not in DECLARED_EXPOSURES:
        raise ExposureTapeError(f"undeclared exposure type {etype!r}")
    spec = DECLARED_EXPOSURES[etype]
    pathway = (target or {}).get("pathway", spec["pathway"])
    node = world.setdefault("pathways", {}).setdefault(pathway, {"on": True, "rate": 1.0})
    factor = spec["factor"] ** magnitude
    node["rate"] = float(node.get("rate", 1.0)) * factor
    world.setdefault("exposures", []).append(
        {"type": etype, "pathway": pathway, "factor": factor, "magnitude": magnitude}
    )


def apply_tape_at_dap(world: dict, tape: dict | None, dap: int) -> None:
    if not tape:
        return
    valid = validate_tape(tape)
    for event in valid["exposures"]:
        when = event["dap"] if event["dap"] is not None else event["t"]
        if int(when) != int(dap):
            continue
        apply_exposure(world, event["type"], event["magnitude"], event["target"])


def transcribe_telemetry(samples: list[dict]) -> dict:
    """Map live telemetry onto declared exposures. Unknown metrics are dropped, not applied."""
    events = []
    for sample in samples:
        metric = sample.get("metric")
        mapping = {
            "cluster_cpu_heat": "heat_pulse",
            "disk_pressure": "drought",
            "error_burst": "pathogen",
            "high_qps": "high_light",
            "queue_depth": "nutrient_n",
        }
        if metric not in mapping:
            continue
        events.append(
            {
                "type": mapping[metric],
                "t": int(sample.get("t", sample.get("dap", 0))),
                "dap": int(sample.get("dap", sample.get("t", 0))),
                "magnitude": float(sample.get("magnitude", 1.0)),
                "target": {},
            }
        )
    return record_tape(events, metadata={"source": "telemetry"})
