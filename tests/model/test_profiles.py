from __future__ import annotations

import pytest

from epik.model.enums import RECIPROCAL_PAIRS
from epik.model.invariants import check_initialized_world
from epik.model.profile import default_profile
from epik.model.world import init_cross_world, validate_profile


def test_default_profile_validates():
    profile = default_profile()
    validate_profile(profile)
    assert profile["id"] == "arabidopsis-gehring-v1"


def test_lyrata_rejected_as_gehring_profile():
    profile = default_profile()
    profile["species"] = "Arabidopsis lyrata"
    with pytest.raises(ValueError, match="thaliana"):
        validate_profile(profile)


@pytest.mark.parametrize("maternal,paternal", RECIPROCAL_PAIRS)
def test_init_cross_invariants(maternal, paternal):
    world = init_cross_world(maternal, paternal)
    check_initialized_world(world)
    assert world["maternal"] == maternal
    assert world["paternal"] == paternal
    assert world["cross_id"] == f"{maternal}x{paternal}"
    egg = world["compartments"]["egg"]["copies"][0]
    assert egg["parent_of_origin"] == "maternal"
    assert egg["accession"] == maternal
    sperm = world["compartments"]["sperm_a"]["copies"][0]
    assert sperm["parent_of_origin"] == "paternal"
    assert sperm["accession"] == paternal
