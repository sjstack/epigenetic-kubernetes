from __future__ import annotations

from epik.mechanisms.chromatin import apply_ros1_sensor_feedback, demethylate_targets, produce_srna
from epik.mechanisms.common import commit_world, divide_population
from epik.model.methylome import dyad_fraction, site_fraction
from epik.model.world import init_cross_world, make_compartment, make_copy


def locus_chromatin(world: dict, loc_id: str) -> str:
    return world["profile_loci"][loc_id].get("chromatin", "euchromatin")


def track_methylome(copies: list[dict], world: dict) -> dict:
    euch_cg, het_cg, het_chh, euch_chh = [], [], [], []
    for copy in copies:
        for loc_id, loc in copy["loci"].items():
            chrom = locus_chromatin(world, loc_id)
            cg = dyad_fraction(loc["cg"])
            chh = site_fraction(loc["chh"])
            if chrom == "heterochromatin":
                het_cg.append(cg)
                het_chh.append(chh)
            else:
                euch_cg.append(cg)
                euch_chh.append(chh)
    def _avg(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "euch_cg": _avg(euch_cg),
        "het_cg": _avg(het_cg),
        "het_chh": _avg(het_chh),
        "euch_chh": _avg(euch_chh),
    }


def make_vegetative_world(profile: dict, accession: str = "C24", perturbations: dict | None = None) -> dict:
    world = init_cross_world(accession, accession, profile=profile, perturbations=perturbations)
    veg = make_compartment(
        "vegetative",
        [
            make_copy("veg-m", accession, "maternal", profile),
            make_copy("veg-p", accession, "paternal", profile),
        ],
        pedigree_terminal=False,
    )
    world["compartments"] = {"vegetative": veg}
    world["stage"] = "vegetative"
    world["lineage"] = {"generation": 0, "protocol": "ros1-homeostasis"}
    world["seed"] = None
    world["trajectory"] = []
    return world


def run_ros1_homeostasis(engine, world: dict, generations: int = 5, divisions: int = 3) -> dict:
    """Separate protocol: never mixed with imprinting claims."""
    world["lineage"]["protocol"] = "ros1-homeostasis"
    selection_only = bool(world.get("perturbations", {}).get("selection_only"))
    sensor = world["pathways"]["ROS1"].get("sensor", True) and world["pathways"]["ROS1"].get("on", True)
    copies = world["compartments"]["vegetative"]["copies"]
    locspec = world["profile_loci"]
    world["trajectory"].append({**track_methylome(copies, world), "generation": 0})

    if not sensor and not selection_only:
        # Broken sensor destabilizes euchromatic maintenance (Williams 2017 scars).
        world["pathways"]["MET1"]["rate"] = 0.62
        world["pathways"]["ROS1"]["on"] = False

    for gen in range(generations):
        if not selection_only:
            produce_srna(world)
            for step in range(divisions):
                rng = engine.rng.stream("ros1-homeostasis", gen, step)
                divide_population(copies, world, rng, locspec)
            if sensor:
                apply_ros1_sensor_feedback(world)
                rng = engine.rng.stream("ros1-homeostasis", "restore", gen)
                demethylate_targets(world, copies, dme=False, ros1=True, rng=rng)
        snapshot = track_methylome(copies, world)
        snapshot["generation"] = gen + 1
        world["trajectory"].append(snapshot)
        world["lineage"]["generation"] = gen + 1
        commit_world(engine, world, "ros1-homeostasis")
    world["stage"] = "ros1-homeostasis-complete"
    world["protocol_firewall"] = "imprinting_claims_forbidden"
    commit_world(engine, world, "ros1-homeostasis")
    return world
