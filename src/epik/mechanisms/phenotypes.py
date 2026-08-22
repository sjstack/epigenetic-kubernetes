from __future__ import annotations

from epik.mechanisms.expression import compute_expression


def apply_hdg3_phenotype(world: dict) -> dict:
    expr = world.get("expression") or compute_expression(world)
    hdg3 = expr["endosperm"]["HDG3"]["bulk"]
    frac = hdg3["maternal_fraction"]
    # PEG: maternal fraction well below 2/3 dosage null
    if frac < 0.40:
        status = "PEG"
        cellularization_dap = 4.6
        seed_size = 0.82
        seed_weight = 0.80
        embryo_delay = 0.05
    else:
        status = "biallelic"
        cellularization_dap = 6.1
        seed_size = 1.18
        seed_weight = 1.16
        embryo_delay = 0.45

    mea = expr["endosperm"]["MEA"]["bulk"]
    viability = 0.95 if mea["maternal"] > 3.0 else 0.08

    world["phenotype"] = {
        "HDG3_status": status,
        "HDG3_maternal_fraction": frac,
        "cellularization_dap": cellularization_dap,
        "seed_size": seed_size,
        "seed_weight": seed_weight,
        "embryo_delay": embryo_delay,
        "viability": viability,
        "dap": world.get("dap"),
    }
    if world.get("seed"):
        world["seed"]["endosperm"]["cellularization_dap"] = cellularization_dap
        world["seed"]["embryo"]["delay"] = embryo_delay
    return world["phenotype"]


def induce_hdg3_te_methylation(world: dict) -> None:
    """Restore Cvi-like unmethylated TE to a Col-like methylated state."""
    from epik.model.methylome import dyads_from_fraction

    for copy in _all_seed_copies(world):
        if "HDG3_TE" in copy["loci"]:
            n = len(copy["loci"]["HDG3_TE"]["cg"])
            copy["loci"]["HDG3_TE"]["cg"] = dyads_from_fraction(n, 0.92)


def _all_seed_copies(world: dict) -> list[dict]:
    copies: list[dict] = []
    if world.get("seed"):
        for comp in world["seed"].values():
            copies.extend(comp["copies"])
    for comp in world.get("compartments", {}).values():
        copies.extend(comp.get("copies", []))
    return copies
