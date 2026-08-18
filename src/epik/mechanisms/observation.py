from __future__ import annotations

import math


def _poisson(rng, lam: float) -> int:
    lam = max(0.0, lam)
    if lam == 0:
        return 0
    L = math.exp(-min(lam, 20))
    k = 0
    p = 1.0
    # Knuth for small lambda; Gaussian-ish fallback for large
    if lam > 20:
        return max(0, int(rng.normalvariate(lam, math.sqrt(lam))))
    while p > L:
        k += 1
        p *= rng.random()
    return k - 1


def observe_rnaseq(
    expression: dict,
    rng,
    *,
    coverage: float = 80.0,
    mapping_bias: float = 0.0,
    contamination: float = 0.0,
    coat_expression: dict | None = None,
) -> dict:
    maternal = expression["maternal"] * (1.0 + mapping_bias)
    paternal = expression["paternal"]
    if contamination and coat_expression:
        maternal += contamination * coat_expression.get("maternal", 0.0)
    total_t = maternal + paternal
    if total_t <= 0:
        return {"m_reads": 0, "p_reads": 0, "coverage": 0, "contamination": contamination, "mapping_bias": mapping_bias}
    scale = coverage / max(total_t, 1e-9)
    m_reads = _poisson(rng, maternal * scale)
    p_reads = _poisson(rng, paternal * scale)
    return {
        "m_reads": m_reads,
        "p_reads": p_reads,
        "coverage": m_reads + p_reads,
        "contamination": contamination,
        "mapping_bias": mapping_bias,
        "coat_marker_fraction": contamination,
    }


def observe_wgbs(cg_fraction: float, rng, coverage: int = 20) -> dict:
    meth = sum(1 for _ in range(coverage) if rng.random() < cg_fraction)
    return {"methylated": meth, "coverage": coverage, "fraction": meth / coverage if coverage else 0.0}


def call_imprinting(
    m_reads: int,
    p_reads: int,
    *,
    null_maternal: float = 2 / 3,
    min_coverage: int = 12,
    contamination: float = 0.0,
    coat_marker_fraction: float = 0.0,
) -> dict:
    total = m_reads + p_reads
    flags: list[str] = []
    if total < min_coverage:
        return {
            "call": "low_coverage",
            "maternal_fraction": None,
            "z": None,
            "flags": ["low_coverage"],
            "null_maternal": null_maternal,
            "m_reads": m_reads,
            "p_reads": p_reads,
        }
    frac = m_reads / total
    se = math.sqrt(null_maternal * (1 - null_maternal) / total)
    z = (frac - null_maternal) / se if se else 0.0
    if z > 1.96:
        call = "MEG"
    elif z < -1.96:
        call = "PEG"
    else:
        call = "biallelic"
    if coat_marker_fraction > 0.1 or contamination > 0.1:
        flags.append("seed_coat_contamination")
    if (coat_marker_fraction > 0.1 or contamination > 0.1) and frac > null_maternal:
        flags.append("possible_false_meg")
    return {
        "call": call,
        "maternal_fraction": frac,
        "z": z,
        "flags": flags,
        "null_maternal": null_maternal,
        "m_reads": m_reads,
        "p_reads": p_reads,
    }


def call_world(world: dict, rng, *, contamination: float = 0.0, mapping_bias: float = 0.0) -> dict:
    expr = world["expression"]
    calls: dict = {"endosperm": {}, "embryo": {}}
    observations: list[dict] = []
    for loc_id, regions in expr["endosperm"].items():
        bulk = regions["bulk"]
        coat = expr["seed_coat"][loc_id]["bulk"]
        obs = observe_rnaseq(
            bulk,
            rng,
            mapping_bias=mapping_bias,
            contamination=contamination,
            coat_expression=coat,
        )
        call = call_imprinting(
            obs["m_reads"],
            obs["p_reads"],
            null_maternal=2 / 3,
            contamination=contamination,
            coat_marker_fraction=obs["coat_marker_fraction"],
        )
        calls["endosperm"][loc_id] = {**call, "true_maternal_fraction": bulk["maternal_fraction"]}
        observations.append({"assay": "RNA-seq", "compartment": "endosperm", "locus": loc_id, **obs})
    for loc_id, regions in expr["embryo"].items():
        bulk = regions["bulk"]
        obs = observe_rnaseq(bulk, rng, mapping_bias=mapping_bias)
        call = call_imprinting(obs["m_reads"], obs["p_reads"], null_maternal=0.5)
        calls["embryo"][loc_id] = {**call, "true_maternal_fraction": bulk["maternal_fraction"]}
        observations.append({"assay": "RNA-seq", "compartment": "embryo", "locus": loc_id, **obs})
    world["imprinting_calls"] = calls
    world["observations"] = observations
    return calls
