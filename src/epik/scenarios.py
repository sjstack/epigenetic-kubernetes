from __future__ import annotations

from epik.mechanisms.common import context_means, iter_copies
from epik.simulate import run_cross, run_somatic_scenario


def run_named_scenario(name: str, seed: int = 1):
    if name in {"met1-loss", "cmt3-loss", "wildtype-maintenance", "chh-rebuild"}:
        pert = {}
        if name == "met1-loss":
            pert = {"met1": False}
        if name == "cmt3-loss":
            pert = {"cmt3": False, "suvh": False}
        engine, world = run_somatic_scenario(seed=seed, divisions=5, perturbations=pert)
        copies = iter_copies(world)
        report = {
            "scenario": name,
            "AtSN1": context_means(copies, "AtSN1"),
            "NEUTRAL1": context_means(copies, "NEUTRAL1"),
            "MEA": context_means(copies, "MEA"),
        }
        return engine, world, report

    pert = {}
    if name == "drm2-off":
        pert = {"drm2": False}
    elif name == "nrpd1-off":
        pert = {"nrpd1": False}
    elif name == "ros1-off":
        pert = {"ros1": False}
    elif name == "scrambled-sirna":
        pert = {"scrambled_sirna": True}
    elif name == "dmr-without-effect":
        pert = {}
    elif name == "dme-off":
        pert = {"dme": False}
    elif name == "nrpd1-maternal":
        pert = {"nrpd1_maternal": False}
    elif name == "nrpd1-paternal":
        pert = {"nrpd1_paternal": False}
    else:
        raise KeyError(name)

    engine, world = run_cross("Col-0", "Cvi", seed=seed, to_dap=7, perturbations=pert)
    calls = world["imprinting_calls"]["endosperm"]
    copies = world["seed"]["endosperm"]["copies"]
    report = {
        "scenario": name,
        "calls": {k: v["call"] for k, v in calls.items() if k in {"MEA", "FWA", "PHE1", "HDG3", "ACT7", "DMR_NULL1"}},
        "AtSN1_chh": context_means(copies, "AtSN1")["chh"],
        "NEUTRAL1_chh": context_means(copies, "NEUTRAL1")["chh"],
        "ANTI_SILENCING1_cg": context_means(copies, "ANTI_SILENCING1")["cg"],
        "DMR_NULL1_call": calls["DMR_NULL1"]["call"],
    }
    return engine, world, report
