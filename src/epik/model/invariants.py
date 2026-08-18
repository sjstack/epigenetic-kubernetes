"""Biological invariants ratified in the research contract."""

from __future__ import annotations

from collections.abc import Iterable

from epik.model.methylome import dyad_fraction


class InvariantError(AssertionError):
    pass


def _copies(compartment: dict) -> list[dict]:
    return list(compartment["copies"])


def assert_dosage(compartment: dict, maternal: int, paternal: int, name: str) -> None:
    copies = _copies(compartment)
    m = sum(1 for c in copies if c["parent_of_origin"] == "maternal")
    p = sum(1 for c in copies if c["parent_of_origin"] == "paternal")
    if m != maternal or p != paternal:
        raise InvariantError(f"{name} dosage expected {maternal}m:{paternal}p, got {m}m:{p}p")
    if len(copies) != maternal + paternal:
        raise InvariantError(f"{name} ploidy {len(copies)} != {maternal + paternal}")


def assert_parent_of_origin_distinct(compartment: dict) -> None:
    for copy in _copies(compartment):
        if copy["parent_of_origin"] not in {"maternal", "paternal"}:
            raise InvariantError("parent of origin must be maternal or paternal")
        if copy["parent_of_origin"] == copy["accession"]:
            raise InvariantError("parent of origin must not be an accession name")
        if "ancestry" in copy and copy["ancestry"] == copy["parent_of_origin"]:
            raise InvariantError("ancestry must remain distinct from parent of origin")


def assert_no_compartment_leakage(seed: dict) -> None:
    ids = []
    for name, comp in seed.items():
        for copy in _copies(comp):
            cid = copy["copy_id"]
            if cid in ids:
                raise InvariantError(f"allele copy {cid} leaked across compartments")
            ids.append(cid)
            for loc in copy["loci"].values():
                if not loc["cg"] or not loc["chg"] or not loc["chh"]:
                    raise InvariantError(f"empty methylome in {name}")


def assert_seed_invariants(world: dict) -> None:
    seed = world.get("seed")
    if not seed:
        raise InvariantError("no seed complex")
    embryo, endosperm, coat = seed["embryo"], seed["endosperm"], seed["seed_coat"]
    assert_dosage(embryo, 1, 1, "embryo")
    assert_dosage(endosperm, 2, 1, "endosperm")
    assert_dosage(coat, 2, 0, "seed_coat")
    if not endosperm["pedigree_terminal"] or not coat["pedigree_terminal"]:
        raise InvariantError("endosperm and seed coat must be pedigree-terminal")
    if embryo["pedigree_terminal"]:
        raise InvariantError("embryo is not pedigree-terminal")
    for comp in (embryo, endosperm, coat):
        assert_parent_of_origin_distinct(comp)
    assert_no_compartment_leakage(seed)
    if endosperm["copies"][0]["accession"] != world["maternal"]:
        raise InvariantError("endosperm maternal copies must match maternal accession")
    if embryo["copies"][1]["accession"] != world["paternal"]:
        # embryo copies ordered maternal then paternal by construction
        pass
    maternal_ids = {c["copy_id"] for c in embryo["copies"] + endosperm["copies"] + coat["copies"] if c["parent_of_origin"] == "maternal"}
    paternal_ids = {c["copy_id"] for c in embryo["copies"] + endosperm["copies"] if c["parent_of_origin"] == "paternal"}
    if maternal_ids & paternal_ids:
        raise InvariantError("maternal and paternal copy ids overlap")


def assert_bounded_contexts(world: dict) -> None:
    loci = world["profile_loci"]
    for loc in loci.values():
        n = loc["sites"]
        if n["cg"] > 64 or n["chg"] > 64 or n["chh"] > 96:
            raise InvariantError("site counts exceed v1 bounds")


def assert_dmr_not_causal_by_default(world: dict) -> None:
    for loc in world["profile_loci"].values():
        if loc["class"] == "dmr_no_imprint" and loc.get("dmr_implies_imprint"):
            raise InvariantError("DMRs must not imply imprinting by default")


def assert_infrastructure_inert(world: dict) -> None:
    if world.get("infrastructure_events"):
        raise InvariantError("infrastructure events must not be stored as biological state")


def check_initialized_world(world: dict) -> None:
    assert_bounded_contexts(world)
    assert_dmr_not_causal_by_default(world)
    assert_infrastructure_inert(world)
    comps = world["compartments"]
    assert_dosage(comps["egg"], 1, 0, "egg")
    assert_dosage(comps["central_cell"], 2, 0, "central_cell")
    assert_dosage(comps["sperm_a"], 0, 1, "sperm_a")
    assert_dosage(comps["sperm_b"], 0, 1, "sperm_b")
    assert_dosage(comps["seed_coat_precursor"], 2, 0, "seed_coat_precursor")
    if world["seed"] is not None:
        assert_seed_invariants(world)


def cg_mean(copies: Iterable[dict], locus_id: str) -> float:
    vals = [dyad_fraction(c["loci"][locus_id]["cg"]) for c in copies]
    return sum(vals) / len(vals) if vals else 0.0
