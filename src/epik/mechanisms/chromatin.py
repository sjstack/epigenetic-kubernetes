from __future__ import annotations

from epik.mechanisms.common import (
    apply_active_demethylation,
    commit_world,
    pathway_on,
    pathway_rate,
    rebuild_rddm_chh,
)


def produce_srna(world: dict) -> None:
    world.setdefault("srna", {"maternal": {}, "paternal": {}})
    scrambled = bool(world.get("perturbations", {}).get("scrambled_sirna"))
    for loc_id, spec in world["profile_loci"].items():
        if not spec.get("rddm_target"):
            continue
        if scrambled:
            world["srna"]["maternal"][f"scrambled-{loc_id}"] = 24
            world["srna"]["paternal"][f"scrambled-{loc_id}"] = 24
            continue
        if pathway_on(world, "NRPD1_maternal") and pathway_on(world, "NRPD1"):
            world["srna"]["maternal"][loc_id] = 24
        else:
            world["srna"]["maternal"].pop(loc_id, None)
        if pathway_on(world, "NRPD1_paternal") and pathway_on(world, "NRPD1"):
            world["srna"]["paternal"][loc_id] = 24
        else:
            world["srna"]["paternal"].pop(loc_id, None)


def demethylate_targets(world: dict, copies: list[dict], *, dme: bool, ros1: bool, rng) -> None:
    dme_rate = pathway_rate(world, "DME", 0.92) if dme else 0.0
    ros1_rate = pathway_rate(world, "ROS1", 0.75) if ros1 else 0.0
    dme_ids = [i for i, s in world["profile_loci"].items() if s.get("dme_target")]
    ros1_ids = [i for i, s in world["profile_loci"].items() if s.get("ros1_target")]
    for copy in copies:
        if dme_rate:
            apply_active_demethylation(copy, dme_ids, dme_rate, rng)
        if ros1_rate:
            apply_active_demethylation(copy, ros1_ids, ros1_rate, rng)


def apply_ros1_sensor_feedback(world: dict) -> None:
    """ROS1 promoter methylation induces ROS1 (Williams 2015). Mechanism only."""
    ros1 = world["pathways"].get("ROS1", {})
    if not ros1.get("sensor", True) or not ros1.get("on", True):
        return
    copies = []
    if world.get("seed"):
        copies = world["seed"]["embryo"]["copies"]
    elif "vegetative" in world.get("compartments", {}):
        copies = world["compartments"]["vegetative"]["copies"]
    if not copies:
        return
    from epik.model.methylome import dyad_fraction

    loc_id = "ROS1_PROMOTER" if "ROS1_PROMOTER" in copies[0]["loci"] else "ROS1"
    meth = sum(dyad_fraction(c["loci"][loc_id]["cg"]) for c in copies) / len(copies)
    ros1["rate"] = 0.25 + 0.7 * meth


def run_rddm_and_demethylation(engine, world: dict, tag: str) -> dict:
    produce_srna(world)
    apply_ros1_sensor_feedback(world)
    rng = engine.rng.stream("rddm-chh", tag, world.get("cross_id", "x"))
    rebuild_rddm_chh(world, rng)
    commit_world(engine, world, "rddm")
    return world
