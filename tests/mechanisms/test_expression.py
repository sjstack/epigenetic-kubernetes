from __future__ import annotations

from epik.simulate import run_cross


def _call(world, loc):
    return world["imprinting_calls"]["endosperm"][loc]


def test_biallelic_recovers_dosage_null():
    _, world = run_cross("Col-0", "Ler", seed=1, to_dap=7)
    act = _call(world, "ACT7")
    assert act["call"] == "biallelic"
    assert abs(act["true_maternal_fraction"] - 2 / 3) < 0.05


def test_canonical_imprints():
    _, world = run_cross("Col-0", "Ler", seed=1, to_dap=7)
    assert _call(world, "MEA")["call"] == "MEG"
    assert _call(world, "FWA")["call"] == "MEG"
    assert _call(world, "FIS2")["call"] == "MEG"
    assert _call(world, "PHE1")["call"] == "PEG"


def test_contamination_flags_false_meg():
    _, world = run_cross("Col-0", "Cvi", seed=2, to_dap=7, contamination=0.4)
    flags = _call(world, "ACT7")["flags"]
    assert "possible_false_meg" in flags
    assert "seed_coat_contamination" in flags


def test_maternal_vs_paternal_poliv_not_interchangeable():
    _, mat = run_cross("Col-0", "Cvi", seed=3, to_dap=7, perturbations={"nrpd1_maternal": False})
    _, pat = run_cross("Col-0", "Cvi", seed=3, to_dap=7, perturbations={"nrpd1_paternal": False})
    m = _call(mat, "PHE1")["true_maternal_fraction"]
    p = _call(pat, "PHE1")["true_maternal_fraction"]
    assert abs(m - p) > 0.02
    # maternal Pol IV loss strengthens paternal contribution (lower maternal fraction)
    _, wt = run_cross("Col-0", "Cvi", seed=3, to_dap=7)
    w = _call(wt, "PHE1")["true_maternal_fraction"]
    assert m < w
    assert p > w
