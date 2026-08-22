from __future__ import annotations

from epik.mechanisms.common import context_means, iter_copies
from epik.simulate import run_somatic_scenario


def _means(world, loc):
    return context_means(iter_copies(world), loc)


def test_high_but_imperfect_cg_maintenance():
    _, world = run_somatic_scenario(seed=1, divisions=5, perturbations={})
    ats = _means(world, "AtSN1")
    assert ats["cg"] > 0.70


def test_met1_loss_progressive_cg():
    _, wt = run_somatic_scenario(seed=2, divisions=5, perturbations={})
    _, mut = run_somatic_scenario(seed=2, divisions=5, perturbations={"met1": False})
    assert _means(mut, "AtSN1")["cg"] < _means(wt, "AtSN1")["cg"] - 0.15


def test_cmt3_suvh_loss_chg():
    _, wt = run_somatic_scenario(seed=3, divisions=5, perturbations={})
    _, mut = run_somatic_scenario(seed=3, divisions=5, perturbations={"cmt3": False, "suvh": False})
    assert _means(mut, "AtSN1")["chg"] < _means(wt, "AtSN1")["chg"] - 0.05


def test_chh_dilution_rebuild_asymmetry():
    _, wt = run_somatic_scenario(seed=4, divisions=4, perturbations={})
    _, drm = run_somatic_scenario(seed=4, divisions=4, perturbations={"drm2": False, "cmt2": False})
    assert _means(wt, "AtSN1")["chh"] > _means(drm, "AtSN1")["chh"]
    assert _means(wt, "AtSN1")["cg"] > 0.5


def test_neutral_locus_not_rddm_dependent():
    _, wt = run_somatic_scenario(seed=5, divisions=4, perturbations={})
    _, drm = run_somatic_scenario(seed=5, divisions=4, perturbations={"drm2": False, "nrpd1": False})
    delta_te = abs(_means(wt, "AtSN1")["chh"] - _means(drm, "AtSN1")["chh"])
    delta_n = abs(_means(wt, "NEUTRAL1")["chh"] - _means(drm, "NEUTRAL1")["chh"])
    assert delta_te > delta_n
