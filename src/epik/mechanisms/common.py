from __future__ import annotations

from copy import deepcopy

from epik.engine.engine import Engine
from epik.engine.intents import Intent
from epik.model.methylome import (
    actively_demethylate,
    dyad_fraction,
    maintain_dyads,
    rebuild_sites,
    replicate_chh,
    replicate_dyads,
    site_fraction,
)


def commit_world(engine: Engine, world: dict, mechanism: str) -> None:
    engine.commit(
        Intent(
            kind="set_world",
            mechanism=mechanism,
            entity_id=str(world.get("cross_id", "world")),
            payload={"world": deepcopy(world)},
            logical_time=engine.clock.t,
        )
    )


def pathway_on(world: dict, name: str) -> bool:
    spec = world["pathways"].get(name)
    if spec is None:
        return False
    return bool(spec.get("on", True))


def pathway_rate(world: dict, name: str, default: float = 0.0) -> float:
    spec = world["pathways"].get(name, {})
    if not spec.get("on", True):
        return 0.0
    return float(spec.get("rate", default))


def iter_copies(world: dict) -> list[dict]:
    copies: list[dict] = []
    if world.get("seed"):
        for comp in world["seed"].values():
            if isinstance(comp, dict) and "copies" in comp:
                copies.extend(comp["copies"])
    for comp in world.get("compartments", {}).values():
        if isinstance(comp, dict) and "copies" in comp:
            copies.extend(comp["copies"])
    return copies


def iter_seed_copies(world: dict, compartment: str | None = None) -> list[dict]:
    if not world.get("seed"):
        return []
    if compartment:
        return list(world["seed"][compartment]["copies"])
    copies: list[dict] = []
    for comp in world["seed"].values():
        copies.extend(comp["copies"])
    return copies


def clone_copy(copy: dict, new_id: str) -> dict:
    cloned = deepcopy(copy)
    cloned["copy_id"] = new_id
    return cloned


def replicate_copy(copy: dict) -> None:
    for loc in copy["loci"].values():
        loc["cg"] = replicate_dyads(loc["cg"])
        loc["chg"] = replicate_dyads(loc["chg"])
        loc["chh"] = replicate_chh(loc["chh"])


def maintain_copy(copy: dict, world: dict, rng, locspec: dict) -> None:
    met1 = pathway_rate(world, "MET1", 0.96)
    cmt3 = pathway_rate(world, "CMT3", 0.86) * (1.0 if pathway_on(world, "SUVH") else 0.0)
    cmt2 = pathway_rate(world, "CMT2", 0.58) * (1.0 if pathway_on(world, "DDM1") else 0.15)
    drm2 = pathway_rate(world, "DRM2", 0.72)
    for loc_id, loc in copy["loci"].items():
        spec = locspec[loc_id]
        loc_met1 = met1
        if (
            spec.get("chromatin") == "euchromatin"
            and not pathway_on(world, "ROS1")
            and world.get("lineage", {}).get("protocol") == "ros1-homeostasis"
        ):
            loc_met1 = min(met1, 0.22)
        loc["cg"] = maintain_dyads(loc["cg"], loc_met1, rng)
        h3k9 = float(loc.get("h3k9me2", 0.0))
        chg_rate = cmt3 * (0.35 + 0.65 * h3k9)
        loc["chg"] = maintain_dyads(loc["chg"], chg_rate, rng)
        het = spec.get("chromatin") == "heterochromatin"
        if spec.get("rddm_target"):
            chh_rate = 0.04
            if drm2 and _has_homologous_srna(world, copy, loc_id):
                chh_rate = 0.75 * drm2
        else:
            chh_rate = cmt2 * (0.85 if het else 0.12)
        if spec.get("class") == "neutral":
            chh_rate = min(chh_rate, 0.05)
        loc["chh"] = rebuild_sites(len(loc["chh"]), chh_rate, rng)
        if het:
            loc["h3k9me2"] = min(1.0, 0.2 + 0.9 * dyad_fraction(loc["chg"]))
        else:
            loc["h3k9me2"] = max(0.0, float(loc.get("h3k9me2", 0.0)) * 0.9)


def _has_homologous_srna(world: dict, copy: dict, loc_id: str) -> bool:
    parent = copy["parent_of_origin"]
    pool = world.get("srna", {}).get(parent, {})
    return bool(pool.get(loc_id, 0) > 0)


def divide_population(copies: list[dict], world: dict, rng, locspec: dict) -> None:
    for copy in copies:
        replicate_copy(copy)
        maintain_copy(copy, world, rng, locspec)


def context_means(copies: list[dict], locus_id: str) -> dict[str, float]:
    return {
        "cg": sum(dyad_fraction(c["loci"][locus_id]["cg"]) for c in copies) / len(copies),
        "chg": sum(dyad_fraction(c["loci"][locus_id]["chg"]) for c in copies) / len(copies),
        "chh": sum(site_fraction(c["loci"][locus_id]["chh"]) for c in copies) / len(copies),
    }


def apply_active_demethylation(copy: dict, locus_ids: list[str], rate: float, rng) -> None:
    for loc_id in locus_ids:
        loc = copy["loci"][loc_id]
        loc["cg"] = actively_demethylate(loc["cg"], rate, rng)
        loc["chg"] = actively_demethylate(loc["chg"], rate * 0.4, rng)


def rebuild_rddm_chh(world: dict, rng) -> None:
    copies = iter_seed_copies(world) or iter_copies(world)
    drm2 = pathway_rate(world, "DRM2", 0.72)
    locspec = world["profile_loci"]
    for copy in copies:
        for loc_id, loc in copy["loci"].items():
            spec = locspec[loc_id]
            if not spec.get("rddm_target"):
                continue
            rate = 0.04
            if drm2 and _has_homologous_srna(world, copy, loc_id):
                rate = 0.75 * drm2
            loc["chh"] = rebuild_sites(len(loc["chh"]), rate, rng)
