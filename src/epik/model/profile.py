"""Arabidopsis Gehring-aligned locus panel and pathway defaults."""

from __future__ import annotations

from copy import deepcopy

from epik.model.enums import ACCESSIONS

_N = {"cg": 20, "chg": 8, "chh": 24}


def _m(cg: float, chg: float = 0.35, chh: float = 0.22) -> dict:
    return {"cg": cg, "chg": chg, "chh": chh}


def _acc(col, ler=None, cvi=None, c24=None) -> dict:
    ler = col if ler is None else ler
    cvi = col if cvi is None else cvi
    c24 = col if c24 is None else c24
    return {"Col-0": col, "Ler": ler, "Cvi": cvi, "C24": c24}


def _locus(
    locus_id: str,
    cls: str,
    rule: str,
    *,
    chromatin: str = "euchromatin",
    dme: bool = False,
    ros1: bool = False,
    rddm: bool = False,
    fis: bool = False,
    te: str | None = None,
    agi: str = "",
    meth: dict | None = None,
    variable_imprint: bool = False,
) -> dict:
    base = meth or _acc(_m(0.8))
    return {
        "id": locus_id,
        "agi": agi,
        "class": cls,
        "chromatin": chromatin,
        "expression_rule": rule,
        "dme_target": dme,
        "ros1_target": ros1,
        "rddm_target": rddm,
        "fis_prc2": fis,
        "te_proximal": te,
        "variable_imprint": variable_imprint,
        "sites": dict(_N),
        "accession_methylation": base,
        "dmr_implies_imprint": False,
    }


def default_profile() -> dict:
    loci = [
        _locus("MEA", "meg", "hypomethylation_activates", dme=True, fis=True, te="MEA_TE", agi="AT1G02580", meth=_acc(_m(0.88))),
        _locus("FIS2", "meg", "hypomethylation_activates", dme=True, fis=True, agi="AT2G35670", meth=_acc(_m(0.84))),
        _locus("FWA", "meg", "hypomethylation_activates", dme=True, te="FWA_TE", agi="AT4G25530", meth=_acc(_m(0.9))),
        _locus("PHE1", "peg", "h3k27me3_represses", fis=True, agi="AT1G65330", meth=_acc(_m(0.55, 0.2, 0.1))),
        _locus(
            "HDG3",
            "peg",
            "te_methylation_promotes_paternal",
            te="HDG3_TE",
            agi="AT2G32370",
            variable_imprint=True,
            meth=_acc(_m(0.4, 0.15, 0.1)),
        ),
        _locus("HDG8", "peg", "te_methylation_promotes_paternal", te="HDG8_TE", agi="AT3G03260", variable_imprint=True),
        _locus("HDG9", "meg", "hypomethylation_activates", dme=True, te="HDG9_TE", agi="AT5G17320"),
        _locus("MYB3R2", "meg", "hypomethylation_activates", dme=True, agi="AT4G00540"),
        _locus("AT5G62110", "peg", "te_methylation_promotes_paternal", agi="AT5G62110"),
        _locus("AT3G14205", "meg", "hypomethylation_activates", dme=True, agi="AT3G14205"),
        _locus("AT2G34890", "peg", "constitutive_paternal", agi="AT2G34890"),
        _locus("DME", "pathway", "constitutive", agi="AT5G04560", meth=_acc(_m(0.2, 0.1, 0.05))),
        _locus("ROS1", "ros1_sensor", "ros1_sensor", te="ROS1_PROMOTER", agi="AT2G36490", meth=_acc(_m(0.45))),
        _locus("ROS1_PROMOTER", "ros1_sensor", "ros1_sensor", chromatin="euchromatin", meth=_acc(_m(0.5))),
        _locus("NRPD1", "pathway", "constitutive", agi="AT1G63020", meth=_acc(_m(0.3, 0.1, 0.05))),
        _locus("MET1", "pathway", "constitutive", agi="AT5G49160", meth=_acc(_m(0.25, 0.1, 0.05))),
        _locus("AtSN1", "rddm_target", "silenced_by_methylation", rddm=True, chromatin="heterochromatin", meth=_acc(_m(0.85, 0.7, 0.6))),
        _locus("SDC", "rddm_target", "silenced_by_methylation", rddm=True, agi="AT2G17690", meth=_acc(_m(0.8, 0.55, 0.5))),
        _locus("ACT7", "biallelic", "constitutive", agi="AT5G09810", meth=_acc(_m(0.15, 0.05, 0.02))),
        _locus("UBQ10", "biallelic", "constitutive", agi="AT4G05320", meth=_acc(_m(0.12, 0.04, 0.02))),
        _locus("NEUTRAL1", "neutral", "null", meth=_acc(_m(0.5, 0.2, 0.1))),
        _locus("DMR_NULL1", "dmr_no_imprint", "null", meth=_acc(_m(0.9), _m(0.4), _m(0.2), _m(0.85))),
        _locus("TARGET_SHARED1", "shared_dme_ros1", "hypomethylation_activates", dme=True, ros1=True, meth=_acc(_m(0.75))),
        _locus("ANTI_SILENCING1", "anti_silencing", "hypomethylation_activates", ros1=True, meth=_acc(_m(0.25, 0.1, 0.05))),
        _locus("MEA_TE", "te", "silenced_by_methylation", chromatin="heterochromatin", rddm=True, meth=_acc(_m(0.9, 0.6, 0.5))),
        _locus("FWA_TE", "te", "silenced_by_methylation", chromatin="heterochromatin", rddm=True, meth=_acc(_m(0.92, 0.65, 0.55))),
        _locus(
            "HDG3_TE",
            "te",
            "silenced_by_methylation",
            chromatin="heterochromatin",
            meth=_acc(_m(0.92, 0.7, 0.55), _m(0.88, 0.66, 0.5), _m(0.04, 0.03, 0.02), _m(0.9, 0.68, 0.52)),
        ),
        _locus("HDG8_TE", "te", "silenced_by_methylation", meth=_acc(_m(0.8), _m(0.78), _m(0.15), _m(0.8))),
        _locus("HDG9_TE", "te", "silenced_by_methylation", meth=_acc(_m(0.7))),
        _locus(
            "EUCHROMATIN_SCAR",
            "anti_silencing",
            "null",
            chromatin="euchromatin",
            ros1=True,
            meth=_acc(_m(0.35, 0.1, 0.05)),
        ),
        _locus(
            "HETEROCHROMATIN_CORE",
            "rddm_target",
            "silenced_by_methylation",
            chromatin="heterochromatin",
            rddm=True,
            meth=_acc(_m(0.93, 0.8, 0.7)),
        ),
    ]
    for loc in loci:
        if loc["class"] == "dmr_no_imprint":
            loc["dmr_implies_imprint"] = False

    return {
        "id": "arabidopsis-gehring-v1",
        "schema": "epik.profile.v1",
        "species": "Arabidopsis thaliana",
        "reference": "TAIR10/Araport11",
        "version": "1.0.0",
        "accessions": list(ACCESSIONS),
        "evidence_spine": "docs/biology/EVIDENCE.md",
        "pathways": {
            "MET1": {"rate": 0.96, "evidence": "A"},
            "VIM": {"rate": 0.96, "evidence": "B"},
            "CMT3": {"rate": 0.86, "evidence": "A"},
            "SUVH": {"rate": 1.0, "evidence": "A"},
            "CMT2": {"rate": 0.58, "evidence": "B"},
            "DDM1": {"rate": 1.0, "evidence": "B"},
            "DRM2": {"rate": 0.72, "evidence": "A"},
            "NRPD1": {"rate": 1.0, "evidence": "A"},
            "DME": {"rate": 0.92, "evidence": "A"},
            "ROS1": {"rate": 0.75, "sensor": True, "evidence": "A"},
            "FIS_PRC2": {"rate": 1.0, "evidence": "A"},
        },
        "loci": loci,
        "invariants": {
            "embryo_dosage": "1m:1p",
            "endosperm_dosage": "2m:1p",
            "seed_coat_dosage": "2m",
            "endosperm_pedigree_terminal": True,
            "seed_coat_pedigree_terminal": True,
        },
    }


def locus_index(profile: dict | None = None) -> dict[str, dict]:
    profile = profile or default_profile()
    return {loc["id"]: loc for loc in profile["loci"]}


def dump_default_profile() -> dict:
    return deepcopy(default_profile())
