from __future__ import annotations

from epik.simulate import run_protocol_ros1


def test_ros1_homeostasis_directions():
    _, intact = run_protocol_ros1(seed=1, generations=4, perturbations={})
    _, broken = run_protocol_ros1(seed=1, generations=4, perturbations={"ros1": False, "ros1_sensor": False})
    _, selection = run_protocol_ros1(seed=1, generations=4, perturbations={"selection_only": True})
    assert intact["protocol_firewall"] == "imprinting_claims_forbidden"
    assert abs(intact["trajectory"][-1]["euch_cg"] - intact["trajectory"][0]["euch_cg"]) < 0.15
    assert broken["trajectory"][-1]["euch_cg"] < broken["trajectory"][0]["euch_cg"] - 0.02
    assert broken["trajectory"][-1]["het_chh"] >= min(t["het_chh"] for t in broken["trajectory"]) - 1e-9
    assert selection["trajectory"][-1]["euch_cg"] == selection["trajectory"][0]["euch_cg"]
