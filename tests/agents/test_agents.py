from __future__ import annotations

from epik.agents.coordinator import run_cross_agents
from epik.simulate import run_cross


def test_shuffled_arrival_matches_oracle():
    oracle, _ = run_cross("Col-0", "Cvi", seed=6, to_dap=3)
    a, _ = run_cross_agents("Col-0", "Cvi", seed=6, to_dap=3, arrival_seed=1)
    b, _ = run_cross_agents("Col-0", "Cvi", seed=6, to_dap=3, arrival_seed=99)
    assert a.digest() == oracle.digest()
    assert b.digest() == oracle.digest()


def test_optional_agent_loss_matches_oracle():
    oracle, _ = run_cross("Col-0", "Cvi", seed=6, to_dap=3)
    lost, _ = run_cross_agents("Col-0", "Cvi", seed=6, to_dap=3, drop="ObserverAgent")
    assert lost.digest() == oracle.digest()
