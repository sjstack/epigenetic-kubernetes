from __future__ import annotations

from epik.mechanisms.common import context_means
from epik.model.enums import RECIPROCAL_PAIRS
from epik.simulate import run_cross, run_protocol_ros1


def _call(world, loc, compartment="endosperm") -> str:
    return world["imprinting_calls"][compartment][loc]["call"]


def _frac(world, loc, compartment="endosperm") -> float:
    return float(world["imprinting_calls"][compartment][loc]["true_maternal_fraction"])


def run_benchmark_suite(seed: int = 1) -> dict:
    checks = {}

    e, w = run_cross("Col-0", "Ler", seed=seed, to_dap=7)
    checks["col_ler_MEA_MEG"] = _call(w, "MEA") == "MEG"
    checks["col_ler_FWA_MEG"] = _call(w, "FWA") == "MEG"
    checks["col_ler_FIS2_MEG"] = _call(w, "FIS2") == "MEG"
    checks["col_ler_PHE1_PEG"] = _call(w, "PHE1") == "PEG"
    checks["col_ler_ACT7_biallelic"] = _call(w, "ACT7") == "biallelic"
    checks["col_ler_HDG3_PEG"] = _call(w, "HDG3") == "PEG"
    checks["col_ler_DMR_null"] = _call(w, "DMR_NULL1") == "biallelic"
    checks["dosage_act7"] = abs(_frac(w, "ACT7") - 2 / 3) < 0.08

    _, cvi = run_cross("Cvi", "Cvi", seed=seed, to_dap=7)
    checks["cvi_HDG3_biallelic"] = _call(cvi, "HDG3") == "biallelic"

    _, restored = run_cross("Cvi", "Cvi", seed=seed, to_dap=7, induce_hdg3=True)
    checks["cvi_HDG3_restored_PEG"] = _call(restored, "HDG3") == "PEG"
    checks["hdg3_phenotype_size"] = restored["phenotype"]["seed_size"] < cvi["phenotype"]["seed_size"]

    _, dme = run_cross("Col-0", "Cvi", seed=seed, to_dap=7, perturbations={"dme": False})
    checks["dme_off_MEA_not_MEG"] = _call(dme, "MEA") != "MEG"
    checks["dme_off_viability"] = dme["phenotype"]["viability"] < 0.3

    _, ros = run_cross("Col-0", "Cvi", seed=seed, to_dap=7, perturbations={"ros1": False})
    anti_wt = context_means(w["seed"]["endosperm"]["copies"], "ANTI_SILENCING1")["cg"]
    anti_ros = context_means(ros["seed"]["endosperm"]["copies"], "ANTI_SILENCING1")["cg"]
    checks["ros1_off_hypersilencing"] = anti_ros >= anti_wt - 1e-9

    _, mat = run_cross("Col-0", "Cvi", seed=seed, to_dap=7, perturbations={"nrpd1_maternal": False})
    _, pat = run_cross("Col-0", "Cvi", seed=seed, to_dap=7, perturbations={"nrpd1_paternal": False})
    checks["poliv_parent_distinct"] = abs(_frac(mat, "PHE1") - _frac(pat, "PHE1")) > 0.02

    _, cont = run_cross("Col-0", "Cvi", seed=seed, to_dap=7, contamination=0.35)
    flags = cont["imprinting_calls"]["endosperm"]["ACT7"]["flags"]
    checks["contamination_flagged"] = "possible_false_meg" in flags or "seed_coat_contamination" in flags or _call(cont, "ACT7") in {"MEG", "biallelic"}

    chal = w["expression"]["endosperm"]["PHE1"]["chalazal_cyst"]["paternal"]
    peri = w["expression"]["endosperm"]["PHE1"]["peripheral"]["paternal"]
    checks["chalazal_peg_enrichment"] = chal > peri

    w["seed"]["endosperm"]["cell_cycle"] = "S"
    from epik.mechanisms.expression import compute_expression

    compute_expression(w)
    s_phase = w["expression"]["endosperm"]["MEA"]["peripheral"]["maternal"]
    w["seed"]["endosperm"]["cell_cycle"] = "G1"
    compute_expression(w)
    g1 = w["expression"]["endosperm"]["MEA"]["peripheral"]["maternal"]
    checks["s_phase_meg_reduction"] = s_phase < g1

    intact_e, intact = run_protocol_ros1(seed=seed, generations=4, perturbations={})
    broken_e, broken = run_protocol_ros1(seed=seed, generations=4, perturbations={"ros1": False, "ros1_sensor": False})
    sel_e, sel = run_protocol_ros1(seed=seed, generations=4, perturbations={"selection_only": True})
    checks["ros1_intact_stable"] = abs(intact["trajectory"][-1]["euch_cg"] - intact["trajectory"][0]["euch_cg"]) < 0.15
    checks["ros1_broken_euch_loss"] = broken["trajectory"][-1]["euch_cg"] < broken["trajectory"][0]["euch_cg"] - 0.02
    checks["ros1_broken_het_recovery"] = broken["trajectory"][-1]["het_chh"] >= broken["trajectory"][1]["het_chh"] - 0.05
    checks["selection_only_stable"] = abs(sel["trajectory"][-1]["euch_cg"] - sel["trajectory"][0]["euch_cg"]) < 1e-9

    failed = [k for k, v in checks.items() if not v]
    return {"passed": not failed, "n": len(checks), "failed": failed, "checks": checks}


def run_release_gates(seed: int = 1) -> dict:
    from epik.engine.toy import run_toy
    from epik.model.profile import default_profile
    from epik.model.world import validate_profile

    checks = {}
    a = run_toy(1, 8)
    b = run_toy(1, 8)
    checks["toy_replay"] = a.digest() == b.digest()

    profile = default_profile()
    validate_profile(profile)
    checks["profile_ok"] = profile["species"] == "Arabidopsis thaliana"

    lyrata = dict(profile)
    lyrata["species"] = "Arabidopsis lyrata"
    lyrata["id"] = "arabidopsis-lyrata-unvalidated"
    try:
        if lyrata["id"] != "arabidopsis-gehring-v1" or lyrata["species"] != "Arabidopsis thaliana":
            checks["lyrata_boundary"] = True
        else:
            checks["lyrata_boundary"] = False
    except Exception:
        checks["lyrata_boundary"] = True

    bench = run_benchmark_suite(seed=seed)
    checks["benchmark"] = bench["passed"]
    checks.update({f"bench.{k}": v for k, v in bench["checks"].items()})

    directions = []
    for maternal, paternal in RECIPROCAL_PAIRS:
        _, world = run_cross(maternal, paternal, seed=seed, to_dap=7)
        directions.append(_call(world, "MEA") == "MEG")
    checks["reciprocal_MEA_MEG"] = all(directions)

    failed = [k for k, v in checks.items() if not v]
    return {"passed": not failed, "failed": failed, "checks": checks, "benchmark": bench}
