from __future__ import annotations

from epik.mechanisms.expression import compute_expression
from epik.simulate import run_cross


def test_hdg3_col_ler_peg_cvi_biallelic_restoration():
    _, col = run_cross("Col-0", "Ler", seed=1, to_dap=7)
    _, cvi = run_cross("Cvi", "Cvi", seed=1, to_dap=7)
    _, restored = run_cross("Cvi", "Cvi", seed=1, to_dap=7, induce_hdg3=True)
    assert col["imprinting_calls"]["endosperm"]["HDG3"]["call"] == "PEG"
    assert cvi["imprinting_calls"]["endosperm"]["HDG3"]["call"] == "biallelic"
    assert restored["imprinting_calls"]["endosperm"]["HDG3"]["call"] == "PEG"
    assert restored["phenotype"]["seed_size"] < cvi["phenotype"]["seed_size"]
    assert restored["phenotype"]["cellularization_dap"] < cvi["phenotype"]["cellularization_dap"]


def test_chalazal_peg_enrichment_and_s_phase_meg_reduction():
    _, world = run_cross("Col-0", "Ler", seed=2, to_dap=7)
    chal = world["expression"]["endosperm"]["PHE1"]["chalazal_cyst"]["paternal"]
    peri = world["expression"]["endosperm"]["PHE1"]["peripheral"]["paternal"]
    assert chal > peri
    world["seed"]["endosperm"]["cell_cycle"] = "S"
    compute_expression(world)
    s_m = world["expression"]["endosperm"]["MEA"]["peripheral"]["maternal"]
    world["seed"]["endosperm"]["cell_cycle"] = "G1"
    compute_expression(world)
    g1_m = world["expression"]["endosperm"]["MEA"]["peripheral"]["maternal"]
    assert s_m < g1_m


def test_held_out_cross_direction_mea():
    _, a = run_cross("Col-0", "Cvi", seed=3, to_dap=7)
    _, b = run_cross("Cvi", "Col-0", seed=3, to_dap=7)
    assert a["imprinting_calls"]["endosperm"]["MEA"]["call"] == "MEG"
    assert b["imprinting_calls"]["endosperm"]["MEA"]["call"] == "MEG"
    assert abs(
        a["imprinting_calls"]["endosperm"]["MEA"]["true_maternal_fraction"]
        - b["imprinting_calls"]["endosperm"]["MEA"]["true_maternal_fraction"]
    ) < 0.15
