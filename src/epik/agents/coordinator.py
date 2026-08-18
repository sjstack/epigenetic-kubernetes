from __future__ import annotations

import random
from collections.abc import Callable
from copy import deepcopy

from epik.engine.engine import Engine
from epik.mechanisms.chromatin import produce_srna, run_rddm_and_demethylation
from epik.mechanisms.common import commit_world
from epik.mechanisms.expression import compute_expression
from epik.mechanisms.observation import call_world
from epik.mechanisms.phenotypes import apply_hdg3_phenotype
from epik.mechanisms.reproduction import (
    apply_central_cell_dme,
    apply_sperm_ros1,
    double_fertilize,
    progress_dap,
)
from epik.model.invariants import assert_seed_invariants, check_initialized_world
from epik.model.world import init_cross_world, load_profile
from epik.simulate import new_engine, run_cross


class Agent:
    def __init__(self, name: str, fn: Callable, required: bool = True) -> None:
        self.name = name
        self.fn = fn
        self.required = required


CANONICAL = [
    "DMEAgent",
    "ROS1Agent",
    "MethylationAgent",
    "PolIVAgent",
    "ExpressionAgent",
    "SeedPhenotypeAgent",
]


def _phase(engine: Engine, world: dict, agents: list[Agent], arrival_seed: int) -> None:
    arrived = list(agents)
    random.Random(arrival_seed).shuffle(arrived)
    by_name = {agent.name: agent for agent in arrived}
    for name in CANONICAL:
        if name in by_name:
            by_name[name].fn(engine, world)
    for agent in arrived:
        if agent.name not in CANONICAL:
            agent.fn(engine, world)


def run_cross_agents(
    maternal: str,
    paternal: str,
    *,
    seed: int = 1,
    to_dap: int = 7,
    arrival_seed: int = 99,
    drop: str | None = None,
    perturbations: dict | None = None,
) -> tuple[Engine, dict]:
    """Coordinator-barriered agents. Arrival order is shuffled; apply order is sorted/canonical."""
    profile = load_profile()
    world = init_cross_world(maternal, paternal, profile=profile, perturbations=perturbations)
    check_initialized_world(world)
    engine = new_engine(seed, world)
    commit_world(engine, world, "init")

    observer = Agent("ObserverAgent", lambda e, w: None, required=False)
    agents = [
        Agent("DMEAgent", lambda e, w: apply_central_cell_dme(e, w)),
        Agent("ROS1Agent", lambda e, w: apply_sperm_ros1(e, w)),
        observer,
    ]
    if drop:
        agents = [a for a in agents if a.name != drop]
    _phase(engine, world, agents, arrival_seed)

    Agent("MethylationAgent", lambda e, w: double_fertilize(e, w)).fn(engine, world)
    assert_seed_invariants(world)

    for dap in [d for d in (3, 5, 7) if d <= to_dap]:
        def rddm(e, w, dap=dap):
            produce_srna(w)
            run_rddm_and_demethylation(e, w, tag=f"dap{dap}")

        def expr(e, w, dap=dap):
            progress_dap(w, dap)
            compute_expression(w)

        def phen(e, w, dap=dap):
            rng = e.rng.stream("observe", w["cross_id"], dap)
            call_world(w, rng)
            apply_hdg3_phenotype(w)
            commit_world(e, w, f"dap-{dap}")

        _phase(
            engine,
            world,
            [
                Agent("PolIVAgent", rddm),
                Agent("ExpressionAgent", expr),
                Agent("SeedPhenotypeAgent", phen),
                Agent("FISPRC2Agent", lambda e, w: None, required=False),
            ],
            arrival_seed + dap,
        )
    engine.state["world"] = deepcopy(world)
    return engine, world


def oracle_digest(maternal: str, paternal: str, seed: int = 1, to_dap: int = 7) -> str:
    engine, _ = run_cross(maternal, paternal, seed=seed, to_dap=to_dap)
    return engine.digest()
