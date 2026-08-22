from __future__ import annotations

from epik.mechanisms.common import context_means
from epik.scenarios import run_named_scenario
from epik.simulate import run_cross


def test_drm2_nrpd1_lose_rddm_targets():
    _, wt = run_cross("Col-0", "Cvi", seed=1, to_dap=7)
    _, drm, _ = run_named_scenario("drm2-off", seed=1)
    _, pol, _ = run_named_scenario("nrpd1-off", seed=1)
    wt_chh = context_means(wt["seed"]["endosperm"]["copies"], "AtSN1")["chh"]
    drm_chh = context_means(drm["seed"]["endosperm"]["copies"], "AtSN1")["chh"]
    pol_chh = context_means(pol["seed"]["endosperm"]["copies"], "AtSN1")["chh"]
    assert drm_chh < wt_chh or pol_chh < wt_chh


def test_ros1_off_hyper_anti_silencing():
    _, wt = run_cross("Col-0", "Cvi", seed=2, to_dap=7)
    _, ros, report = run_named_scenario("ros1-off", seed=2)
    wt_cg = context_means(wt["seed"]["endosperm"]["copies"], "ANTI_SILENCING1")["cg"]
    ros_cg = context_means(ros["seed"]["endosperm"]["copies"], "ANTI_SILENCING1")["cg"]
    assert ros_cg >= wt_cg - 1e-9
    assert report["ANTI_SILENCING1_cg"] == ros_cg


def test_scrambled_sirna_no_homology():
    _, wt = run_cross("Col-0", "Cvi", seed=3, to_dap=7)
    _, scr, _ = run_named_scenario("scrambled-sirna", seed=3)
    wt_chh = context_means(wt["seed"]["endosperm"]["copies"], "AtSN1")["chh"]
    scr_chh = context_means(scr["seed"]["endosperm"]["copies"], "AtSN1")["chh"]
    assert scr_chh <= wt_chh + 1e-9


def test_dmr_without_imprinting_effect():
    _, _, report = run_named_scenario("dmr-without-effect", seed=4)
    assert report["DMR_NULL1_call"] == "biallelic"
