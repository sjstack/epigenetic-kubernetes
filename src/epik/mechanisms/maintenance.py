from __future__ import annotations

from epik.mechanisms.chromatin import produce_srna
from epik.mechanisms.common import commit_world, divide_population, iter_copies


def run_somatic_divisions(engine, world: dict, divisions: int, mechanism: str = "maintenance") -> dict:
    locspec = world["profile_loci"]
    for step in range(divisions):
        rng = engine.rng.stream("maintenance", world.get("cross_id", "veg"), step)
        produce_srna(world)
        divide_population(iter_copies(world), world, rng, locspec)
        world["stage"] = f"somatic_division_{step + 1}"
        world["division"] = step + 1
        commit_world(engine, world, mechanism)
    return world


def met1_off(world: dict) -> None:
    world["pathways"]["MET1"]["on"] = False


def cmt3_off(world: dict) -> None:
    world["pathways"]["CMT3"]["on"] = False
    world["pathways"]["SUVH"]["on"] = False
