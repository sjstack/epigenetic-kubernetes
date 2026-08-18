from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from epik.model.enums import canonical_accession
from epik.model.methylome import dyads_from_fraction, sites_from_fraction
from epik.model.profile import default_profile, locus_index
from epik.paths import profiles_dir


def load_profile(path: str | Path | None = None) -> dict:
    if path is None:
        candidate = profiles_dir() / "arabidopsis-gehring-v1" / "profile.json"
        if candidate.exists():
            return json.loads(candidate.read_text())
        return default_profile()
    path = Path(path)
    if path.is_dir():
        path = path / "profile.json"
    data = json.loads(path.read_text())
    validate_profile(data)
    return data


def validate_profile(profile: dict) -> None:
    required = {"id", "schema", "species", "accessions", "loci", "pathways"}
    missing = required - set(profile)
    if missing:
        raise ValueError(f"profile missing keys: {sorted(missing)}")
    if not profile["loci"]:
        raise ValueError("profile has no loci")
    ids = [loc["id"] for loc in profile["loci"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate locus ids")
    for loc in profile["loci"]:
        for key in ("class", "expression_rule", "accession_methylation", "sites"):
            if key not in loc:
                raise ValueError(f"locus {loc.get('id')} missing {key}")
        te = loc.get("te_proximal")
        if te and te not in ids:
            raise ValueError(f"locus {loc['id']} te_proximal {te} is not a locus")
    if profile.get("id") == "arabidopsis-gehring-v1" and profile.get("species") != "Arabidopsis thaliana":
        raise ValueError("arabidopsis-gehring-v1 is Arabidopsis thaliana only")


def _copy_loci(accession: str, profile: dict) -> dict:
    loci = {}
    for loc in profile["loci"]:
        meth = loc["accession_methylation"][accession]
        sites = loc["sites"]
        h3k9 = 0.75 if loc["chromatin"] == "heterochromatin" else 0.12
        h3k27 = 0.0
        loci[loc["id"]] = {
            "cg": dyads_from_fraction(sites["cg"], meth["cg"]),
            "chg": dyads_from_fraction(sites["chg"], meth["chg"]),
            "chh": sites_from_fraction(sites["chh"], meth["chh"]),
            "h3k27me3": h3k27,
            "h3k9me2": h3k9,
        }
    return loci


def make_copy(copy_id: str, accession: str, parent: str, profile: dict) -> dict:
    return {
        "copy_id": copy_id,
        "accession": accession,
        "parent_of_origin": parent,
        "haplotype": accession,
        "loci": _copy_loci(accession, profile),
    }


def make_compartment(name: str, copies: list[dict], **extra) -> dict:
    maternal = sum(1 for c in copies if c["parent_of_origin"] == "maternal")
    paternal = sum(1 for c in copies if c["parent_of_origin"] == "paternal")
    payload = {
        "name": name,
        "copies": copies,
        "ploidy": len(copies),
        "maternal_copies": maternal,
        "paternal_copies": paternal,
        "pedigree_terminal": name in {"endosperm", "seed_coat"},
        "cell_cycle": "G1",
        "region": extra.pop("region", None),
        "dap": extra.pop("dap", 0),
    }
    payload.update(extra)
    return payload


def default_pathways(profile: dict, perturbations: dict | None = None) -> dict:
    paths = {}
    for name, spec in profile["pathways"].items():
        paths[name] = {"on": True, **deepcopy(spec)}
    paths["NRPD1_maternal"] = {"on": True, "rate": 1.0}
    paths["NRPD1_paternal"] = {"on": True, "rate": 1.0}
    perturbations = perturbations or {}
    for key, val in perturbations.items():
        if key in paths:
            if isinstance(val, bool):
                paths[key]["on"] = val
            elif isinstance(val, dict):
                paths[key].update(val)
        elif key == "nrpd1_maternal":
            paths["NRPD1_maternal"]["on"] = bool(val)
        elif key == "nrpd1_paternal":
            paths["NRPD1_paternal"]["on"] = bool(val)
        elif key in {"met1", "cmt3", "suvh", "cmt2", "drm2", "nrpd1", "dme", "ros1", "fis_prc2", "ddm1"}:
            canon = key.upper() if key != "fis_prc2" else "FIS_PRC2"
            if canon == "NRPD1":
                paths["NRPD1_maternal"]["on"] = bool(val)
                paths["NRPD1_paternal"]["on"] = bool(val)
                paths["NRPD1"]["on"] = bool(val)
            else:
                paths[canon]["on"] = bool(val)
        elif key == "ros1_sensor":
            paths["ROS1"]["sensor"] = bool(val)
    return paths


def init_cross_world(
    maternal: str,
    paternal: str,
    profile: dict | None = None,
    perturbations: dict | None = None,
    replicate: int = 1,
) -> dict:
    profile = profile or load_profile()
    maternal = canonical_accession(maternal)
    paternal = canonical_accession(paternal)
    egg = make_compartment("egg", [make_copy("egg-m", maternal, "maternal", profile)])
    polar_a = make_copy("polar-a", maternal, "maternal", profile)
    polar_b = make_copy("polar-b", maternal, "maternal", profile)
    central = make_compartment("central_cell", [polar_a, polar_b])
    sperm_a = make_compartment("sperm_a", [make_copy("sperm-a", paternal, "paternal", profile)])
    sperm_b = make_compartment("sperm_b", [make_copy("sperm-b", paternal, "paternal", profile)])
    coat_pre = make_compartment(
        "seed_coat_precursor",
        [
            make_copy("coat-m1", maternal, "maternal", profile),
            make_copy("coat-m2", maternal, "maternal", profile),
        ],
    )
    return {
        "schema": "epik.world.v1",
        "profile_id": profile["id"],
        "profile_version": profile.get("version", "1.0.0"),
        "maternal": maternal,
        "paternal": paternal,
        "cross_id": f"{maternal}x{paternal}",
        "cross_direction": f"{maternal}x{paternal}",
        "replicate": replicate,
        "dap": 0,
        "stage": "gametophytes",
        "pathways": default_pathways(profile, perturbations),
        "perturbations": perturbations or {},
        "profile_loci": locus_index(profile),
        "compartments": {
            "egg": egg,
            "central_cell": central,
            "sperm_a": sperm_a,
            "sperm_b": sperm_b,
            "seed_coat_precursor": coat_pre,
        },
        "seed": None,
        "srna": {"maternal": {}, "paternal": {}},
        "expression": {},
        "observations": [],
        "imprinting_calls": {},
        "phenotype": {},
        "exposures": [],
        "lineage": {"generation": 0, "protocol": None},
        "fertilization_committed": False,
    }


def all_reciprocal_cross_defs(profile: dict | None = None) -> list[dict]:
    from epik.model.enums import RECIPROCAL_PAIRS

    profile = profile or load_profile()
    out = []
    for maternal, paternal in RECIPROCAL_PAIRS:
        out.append(
            {
                "schema": "epik.cross.v1",
                "maternal": maternal,
                "paternal": paternal,
                "cross_id": f"{maternal}x{paternal}",
                "profile_id": profile["id"],
                "embryo_dosage": "1m:1p",
                "endosperm_dosage": "2m:1p",
                "seed_coat_dosage": "2m",
            }
        )
    return out


def write_world(path: Path, world: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(world, indent=2, sort_keys=True))
