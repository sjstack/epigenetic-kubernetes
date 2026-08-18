from __future__ import annotations

from enum import Enum


class ParentOfOrigin(str, Enum):
    MATERNAL = "maternal"
    PATERNAL = "paternal"


class Compartment(str, Enum):
    EGG = "egg"
    CENTRAL_CELL = "central_cell"
    SPERM_A = "sperm_a"
    SPERM_B = "sperm_b"
    SEED_COAT_PRECURSOR = "seed_coat_precursor"
    EMBRYO = "embryo"
    ENDOSPERM = "endosperm"
    SEED_COAT = "seed_coat"
    VEGETATIVE = "vegetative"


class EndospermRegion(str, Enum):
    PERIPHERAL = "peripheral"
    MICROPYLAR = "micropylar"
    CHALAZAL_CYST = "chalazal_cyst"
    CHALAZAL_NODULE = "chalazal_nodule"


class CellCyclePhase(str, Enum):
    G1 = "G1"
    S = "S"
    G2 = "G2"
    M = "M"


class LocusClass(str, Enum):
    MEG = "meg"
    PEG = "peg"
    BIALLELIC = "biallelic"
    TE = "te"
    DMR_NO_IMPRINT = "dmr_no_imprint"
    PATHWAY = "pathway"
    ANTI_SILENCING = "anti_silencing"
    RDDM_TARGET = "rddm_target"
    NEUTRAL = "neutral"
    ROS1_SENSOR = "ros1_sensor"
    SHARED_DME_ROS1 = "shared_dme_ros1"


class ChromatinClass(str, Enum):
    EUCHROMATIN = "euchromatin"
    HETEROCHROMATIN = "heterochromatin"


class ExpressionRule(str, Enum):
    HYPO_ACTIVATES = "hypomethylation_activates"
    K27_REPRESSES = "h3k27me3_represses"
    TE_METH_PEG = "te_methylation_promotes_paternal"
    CONSTITUTIVE = "constitutive"
    NULL = "null"
    SILENCED_BY_METH = "silenced_by_methylation"
    SENSOR = "ros1_sensor"
    CONSTITUTIVE_PATERNAL = "constitutive_paternal"


ACCESSIONS = ("Col-0", "Ler", "Cvi", "C24")
RECIPROCAL_PAIRS = (
    ("Col-0", "Ler"),
    ("Ler", "Col-0"),
    ("Col-0", "Cvi"),
    ("Cvi", "Col-0"),
    ("Ler", "Cvi"),
    ("Cvi", "Ler"),
)

ALIAS = {
    "Col": "Col-0",
    "Col-0": "Col-0",
    "Col0": "Col-0",
    "Ler": "Ler",
    "Cvi": "Cvi",
    "C24": "C24",
}


def canonical_accession(name: str) -> str:
    key = name.strip()
    if key not in ALIAS:
        raise ValueError(f"unknown accession {name!r}")
    return ALIAS[key]


def parse_cross(token: str) -> tuple[str, str]:
    raw = token.replace("X", "x")
    if "x" not in raw:
        raise ValueError(f"cross token must look like ColxCvi, got {token!r}")
    left, right = raw.split("x", 1)
    return canonical_accession(left), canonical_accession(right)
