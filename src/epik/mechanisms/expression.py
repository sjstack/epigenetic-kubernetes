from __future__ import annotations

from epik.mechanisms.common import pathway_on
from epik.model.methylome import dyad_fraction


def allele_expression(spec: dict, copy: dict, world: dict, *, region: str, phase: str) -> float:
    loc_id = spec["id"]
    loc = copy["loci"][loc_id]
    cg = dyad_fraction(loc["cg"])
    k27 = float(loc.get("h3k27me3", 0.0))
    parent = copy["parent_of_origin"]
    rule = spec["expression_rule"]
    te_id = spec.get("te_proximal")
    te = dyad_fraction(copy["loci"][te_id]["cg"]) if te_id and te_id in copy["loci"] else cg

    if rule == "hypomethylation_activates":
        expr = 14.0 * ((1.0 - cg) ** 1.4)
        if k27 > 0.5:
            expr *= 0.08
    elif rule == "h3k27me3_represses":
        expr = 13.0 * (1.0 - k27)
    elif rule == "te_methylation_promotes_paternal":
        if te > 0.5:
            expr = 0.7 if parent == "maternal" else 13.0
        else:
            expr = 8.0
    elif rule == "constitutive":
        expr = 8.0
    elif rule == "constitutive_paternal":
        expr = 1.0 if parent == "maternal" else 12.0
    elif rule == "silenced_by_methylation":
        expr = 10.0 * (1.0 - cg)
    elif rule == "ros1_sensor":
        expr = 4.0 + 8.0 * cg
    else:
        expr = 3.0

    if not pathway_on(world, "NRPD1_maternal"):
        expr *= 1.35 if parent == "paternal" else 0.82
    if not pathway_on(world, "NRPD1_paternal"):
        expr *= 1.35 if parent == "maternal" else 0.82

    if region in {"chalazal_cyst", "chalazal_nodule"} and spec["class"] == "peg" and parent == "paternal":
        expr *= 1.55
    if phase == "S" and spec["class"] == "meg" and parent == "maternal":
        expr *= 0.62
    return max(0.0, expr)


def summarize_expression(copies: list[dict], spec: dict, world: dict, region: str, phase: str) -> dict:
    maternal = 0.0
    paternal = 0.0
    for copy in copies:
        value = allele_expression(spec, copy, world, region=region, phase=phase)
        if copy["parent_of_origin"] == "maternal":
            maternal += value
        else:
            paternal += value
    total = maternal + paternal
    return {
        "maternal": maternal,
        "paternal": paternal,
        "total": total,
        "maternal_fraction": (maternal / total) if total else 0.0,
        "n_maternal_copies": sum(1 for c in copies if c["parent_of_origin"] == "maternal"),
        "n_paternal_copies": sum(1 for c in copies if c["parent_of_origin"] == "paternal"),
    }


def compute_expression(world: dict) -> dict:
    if not world.get("seed"):
        return {}
    phase = world["seed"]["endosperm"].get("cell_cycle", "G1")
    regions = world["seed"]["endosperm"].get("regions", ["peripheral"])
    table: dict = {"embryo": {}, "endosperm": {}, "seed_coat": {}}
    for loc_id, spec in world["profile_loci"].items():
        spec = {**spec, "id": loc_id}
        table["embryo"][loc_id] = {
            "bulk": summarize_expression(world["seed"]["embryo"]["copies"], spec, world, "embryo", phase)
        }
        table["seed_coat"][loc_id] = {
            "bulk": summarize_expression(world["seed"]["seed_coat"]["copies"], spec, world, "coat", phase)
        }
        endo = {}
        for region in regions:
            endo[region] = summarize_expression(
                world["seed"]["endosperm"]["copies"], spec, world, region, phase
            )
        endo["bulk"] = endo.get("peripheral") or next(iter(endo.values()))
        table["endosperm"][loc_id] = endo
    world["expression"] = table
    return table
