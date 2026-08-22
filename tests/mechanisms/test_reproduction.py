from __future__ import annotations

import pytest

from epik.mechanisms.common import context_means
from epik.mechanisms.reproduction import IncompleteFertilization, double_fertilize
from epik.model.enums import RECIPROCAL_PAIRS
from epik.model.invariants import assert_seed_invariants
from epik.model.world import init_cross_world
from epik.simulate import new_engine, run_cross


@pytest.mark.parametrize("maternal,paternal", RECIPROCAL_PAIRS)
def test_ploidy_invariants_all_crosses(maternal, paternal):
    _, world = run_cross(maternal, paternal, seed=1, to_dap=7)
    assert_seed_invariants(world)
    emb = world["seed"]["embryo"]
    end = world["seed"]["endosperm"]
    coat = world["seed"]["seed_coat"]
    assert (emb["maternal_copies"], emb["paternal_copies"]) == (1, 1)
    assert (end["maternal_copies"], end["paternal_copies"]) == (2, 1)
    assert (coat["maternal_copies"], coat["paternal_copies"]) == (2, 0)
    ids = [c["copy_id"] for c in emb["copies"] + end["copies"] + coat["copies"]]
    assert len(ids) == len(set(ids))


def test_fertilization_is_atomic():
    world = init_cross_world("Col-0", "Cvi")
    engine = new_engine(1, world)
    world["compartments"]["sperm_b"]["copies"] = []
    with pytest.raises(IncompleteFertilization):
        double_fertilize(engine, world)
    assert world["seed"] is None
    assert world["fertilization_committed"] is False


def test_dme_and_ros1_are_parent_specific():
    _, wt = run_cross("Col-0", "Cvi", seed=2, to_dap=3)
    _, dme = run_cross("Col-0", "Cvi", seed=2, to_dap=3, perturbations={"dme": False})
    _, ros = run_cross("Col-0", "Cvi", seed=2, to_dap=3, perturbations={"ros1": False})
    wt_mea = context_means(wt["seed"]["endosperm"]["copies"], "MEA")["cg"]
    dme_mea = context_means(dme["seed"]["endosperm"]["copies"], "MEA")["cg"]
    assert dme_mea > wt_mea
    wt_anti = context_means(wt["seed"]["endosperm"]["copies"], "ANTI_SILENCING1")["cg"]
    ros_anti = context_means(ros["seed"]["endosperm"]["copies"], "ANTI_SILENCING1")["cg"]
    assert ros_anti >= wt_anti - 1e-9
    # DME-off should not be a ROS1-off synonym: MEA shift is the DME signature.
    ros_mea = context_means(ros["seed"]["endosperm"]["copies"], "MEA")["cg"]
    assert abs(ros_mea - wt_mea) < abs(dme_mea - wt_mea)
