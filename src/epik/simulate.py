from __future__ import annotations

from copy import deepcopy

from epik.engine.engine import Engine
from epik.integration.tape import apply_tape_at_dap
from epik.mechanisms.chromatin import produce_srna, run_rddm_and_demethylation
from epik.mechanisms.common import commit_world
from epik.mechanisms.expression import compute_expression
from epik.mechanisms.maintenance import run_somatic_divisions
from epik.mechanisms.observation import call_world
from epik.mechanisms.phenotypes import apply_hdg3_phenotype, induce_hdg3_te_methylation
from epik.mechanisms.reproduction import (
    apply_central_cell_dme,
    apply_sperm_ros1,
    double_fertilize,
    progress_dap,
)
from epik.mechanisms.ros1 import make_vegetative_world, run_ros1_homeostasis
from epik.model.enums import parse_cross
from epik.model.invariants import assert_seed_invariants, check_initialized_world
from epik.model.world import init_cross_world, load_profile


def new_engine(seed: int, world: dict | None = None) -> Engine:
    engine = Engine(seed=seed)
    if world is not None:
        engine.state["world"] = deepcopy(world)
    return engine


def _dap_loop(engine, world, to_dap, *, from_dap, exposure_tape, contamination, mapping_bias):
    daps = [d for d in (3, 5, 7) if from_dap < d <= to_dap]
    for dap in daps:
        apply_tape_at_dap(world, exposure_tape, dap)
        produce_srna(world)
        run_rddm_and_demethylation(engine, world, tag=f"dap{dap}")
        progress_dap(world, dap)
        compute_expression(world)
        rng = engine.rng.stream("observe", world["cross_id"], dap)
        call_world(world, rng, contamination=contamination, mapping_bias=mapping_bias)
        apply_hdg3_phenotype(world)
        commit_world(engine, world, f"dap-{dap}")
    engine.state["world"] = deepcopy(world)
    return world


def run_cross(
    maternal: str,
    paternal: str,
    *,
    to_dap: int = 7,
    seed: int = 1,
    perturbations: dict | None = None,
    profile: dict | None = None,
    exposure_tape: dict | None = None,
    contamination: float = 0.0,
    mapping_bias: float = 0.0,
    induce_hdg3: bool = False,
) -> tuple[Engine, dict]:
    profile = profile or load_profile()
    world = init_cross_world(maternal, paternal, profile=profile, perturbations=perturbations)
    check_initialized_world(world)
    engine = new_engine(seed, world)
    commit_world(engine, world, "init")

    apply_central_cell_dme(engine, world)
    apply_sperm_ros1(engine, world)
    double_fertilize(engine, world)
    assert_seed_invariants(world)

    if induce_hdg3 or (perturbations or {}).get("induce_hdg3_te_methylation"):
        induce_hdg3_te_methylation(world)
        commit_world(engine, world, "hdg3-induction")

    _dap_loop(
        engine,
        world,
        to_dap,
        from_dap=0,
        exposure_tape=exposure_tape,
        contamination=contamination,
        mapping_bias=mapping_bias,
    )
    return engine, world


def run_cross_token(token: str, **kwargs) -> tuple[Engine, dict]:
    maternal, paternal = parse_cross(token)
    return run_cross(maternal, paternal, **kwargs)


def run_somatic_scenario(
    *,
    seed: int = 1,
    divisions: int = 5,
    perturbations: dict | None = None,
    accession: str = "Col-0",
) -> tuple[Engine, dict]:
    profile = load_profile()
    world = init_cross_world(accession, accession, profile=profile, perturbations=perturbations)
    engine = new_engine(seed, world)
    run_somatic_divisions(engine, world, divisions)
    return engine, world


def run_protocol_ros1(
    *,
    seed: int = 1,
    generations: int = 5,
    perturbations: dict | None = None,
    accession: str = "C24",
) -> tuple[Engine, dict]:
    profile = load_profile()
    world = make_vegetative_world(profile, accession=accession, perturbations=perturbations)
    engine = new_engine(seed, world)
    commit_world(engine, world, "ros1-init")
    run_ros1_homeostasis(engine, world, generations=generations)
    return engine, world


def continue_cross(
    engine: Engine,
    *,
    to_dap: int = 7,
    exposure_tape: dict | None = None,
    contamination: float = 0.0,
    mapping_bias: float = 0.0,
) -> tuple[Engine, dict]:
    world = engine.state["world"]
    from_dap = int(world.get("dap") or 0)
    _dap_loop(
        engine,
        world,
        to_dap,
        from_dap=from_dap,
        exposure_tape=exposure_tape,
        contamination=contamination,
        mapping_bias=mapping_bias,
    )
    return engine, world
