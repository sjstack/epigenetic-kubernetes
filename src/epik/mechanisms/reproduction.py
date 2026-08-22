from __future__ import annotations

from epik.mechanisms.chromatin import demethylate_targets
from epik.mechanisms.common import clone_copy, commit_world
from epik.model.invariants import InvariantError
from epik.model.world import make_compartment


class IncompleteFertilization(InvariantError):
    pass


def apply_central_cell_dme(engine, world: dict) -> dict:
    rng = engine.rng.stream("dme", world["cross_id"])
    demethylate_targets(world, world["compartments"]["central_cell"]["copies"], dme=True, ros1=False, rng=rng)
    world["stage"] = "central_cell_dme"
    commit_world(engine, world, "dme")
    return world


def apply_sperm_ros1(engine, world: dict) -> dict:
    rng = engine.rng.stream("ros1-sperm", world["cross_id"])
    copies = world["compartments"]["sperm_a"]["copies"] + world["compartments"]["sperm_b"]["copies"]
    demethylate_targets(world, copies, dme=False, ros1=True, rng=rng)
    world["stage"] = "sperm_ros1"
    commit_world(engine, world, "ros1")
    return world


def double_fertilize(engine, world: dict) -> dict:
    comps = world["compartments"]
    required = ("egg", "central_cell", "sperm_a", "sperm_b", "seed_coat_precursor")
    for name in required:
        if name not in comps or not comps[name].get("copies"):
            raise IncompleteFertilization(f"missing gamete {name}")
        if comps[name].get("consumed"):
            raise IncompleteFertilization(f"{name} already consumed")
    if world.get("fertilization_committed"):
        raise IncompleteFertilization("fertilization already committed")

    egg = comps["egg"]["copies"][0]
    polars = comps["central_cell"]["copies"]
    if len(polars) != 2:
        raise IncompleteFertilization("central cell must have two polar nuclei")
    sperm_a = comps["sperm_a"]["copies"][0]
    sperm_b = comps["sperm_b"]["copies"][0]
    coat_copies = comps["seed_coat_precursor"]["copies"]

    embryo = make_compartment(
        "embryo",
        [clone_copy(egg, "emb-m"), clone_copy(sperm_a, "emb-p")],
        pedigree_terminal=False,
        dap=0,
    )
    endosperm = make_compartment(
        "endosperm",
        [
            clone_copy(polars[0], "end-m1"),
            clone_copy(polars[1], "end-m2"),
            clone_copy(sperm_b, "end-p"),
        ],
        pedigree_terminal=True,
        dap=0,
        region="peripheral",
        regions=["peripheral", "micropylar", "chalazal_cyst", "chalazal_nodule"],
    )
    coat = make_compartment(
        "seed_coat",
        [clone_copy(coat_copies[0], "coat-1"), clone_copy(coat_copies[1], "coat-2")],
        pedigree_terminal=True,
        dap=0,
    )
    seed = {"embryo": embryo, "endosperm": endosperm, "seed_coat": coat}
    if not (seed["embryo"] and seed["endosperm"] and seed["seed_coat"]):
        raise IncompleteFertilization("atomic fertilization failed")

    _apply_fis_prc2(world, seed)

    world["seed"] = seed
    world["fertilization_committed"] = True
    world["stage"] = "seed"
    world["dap"] = 0
    for name in required:
        comps[name]["consumed"] = True
    commit_world(engine, world, "double_fertilization")
    return world


def _apply_fis_prc2(world: dict, seed: dict) -> None:
    if not world["pathways"].get("FIS_PRC2", {}).get("on", True):
        return
    dme_ok = world["pathways"].get("DME", {}).get("on", True)
    for copy in seed["embryo"]["copies"] + seed["endosperm"]["copies"]:
        for loc_id, spec in world["profile_loci"].items():
            if not spec.get("fis_prc2"):
                continue
            parent = copy["parent_of_origin"]
            if loc_id in {"MEA", "FIS2"} and parent == "paternal":
                copy["loci"][loc_id]["h3k27me3"] = 0.9 if dme_ok else 0.25
            if loc_id == "PHE1" and parent == "maternal":
                copy["loci"][loc_id]["h3k27me3"] = 0.88


def progress_dap(world: dict, dap: int) -> None:
    world["dap"] = dap
    world["stage"] = f"dap_{dap}"
    if not world.get("seed"):
        return
    for name, comp in world["seed"].items():
        comp["dap"] = dap
    if dap >= 5:
        world["seed"]["endosperm"]["cellularizing"] = True
    if dap >= 7:
        world["seed"]["endosperm"]["cellularized"] = True
        world["seed"]["embryo"]["embryo_stage"] = "heart"
    elif dap >= 5:
        world["seed"]["embryo"]["embryo_stage"] = "globular"
    else:
        world["seed"]["embryo"]["embryo_stage"] = "preglobular"
