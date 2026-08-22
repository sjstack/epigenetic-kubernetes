from __future__ import annotations

import json

from epik.model.profile import default_profile
from epik.paths import profiles_dir, schemas_dir


def json_schema_skeleton(title: str, schema_id: str) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "title": title,
        "type": "object",
        "required": ["schema"],
        "properties": {"schema": {"type": "string"}},
        "additionalProperties": True,
    }


SCHEMAS = {
    "epik.world.v1.json": json_schema_skeleton("World state", "epik.world.v1"),
    "epik.event-ledger.v1.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "epik.event-ledger.v1",
        "title": "Event ledger",
        "type": "array",
        "items": {"type": "object", "required": ["index", "kind", "mechanism"]},
    },
    "epik.exposure-tape.v1.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "epik.exposure-tape.v1",
        "title": "Exposure tape",
        "type": "object",
        "required": ["schema", "exposures"],
        "properties": {
            "schema": {"const": "epik.exposure-tape.v1"},
            "exposures": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {
                            "enum": ["heat_pulse", "drought", "pathogen", "high_light", "nutrient_n"]
                        }
                    },
                },
            },
        },
    },
    "epik.cross.v1.json": json_schema_skeleton("Cross definition", "epik.cross.v1"),
    "epik.profile.v1.json": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "epik.profile.v1",
        "title": "Plant profile",
        "type": "object",
        "required": ["id", "schema", "species", "loci", "accessions"],
        "properties": {
            "id": {"type": "string"},
            "schema": {"type": "string"},
            "species": {"type": "string"},
            "loci": {"type": "array"},
            "accessions": {"type": "array"},
        },
        "additionalProperties": True,
    },
    "epik.imprinting-call.v1.json": json_schema_skeleton("Imprinting calls", "epik.imprinting-call.v1"),
    "epik.artifact-manifest.v1.json": json_schema_skeleton("Artifact manifest", "epik.artifact-manifest.v1"),
    "epik.checkpoint.v1.json": json_schema_skeleton("Checkpoint", "epik.checkpoint.v1"),
}


def dump() -> None:
    d = schemas_dir()
    d.mkdir(parents=True, exist_ok=True)
    for name, body in SCHEMAS.items():
        (d / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    prof_dir = profiles_dir() / "arabidopsis-gehring-v1"
    prof_dir.mkdir(parents=True, exist_ok=True)
    (prof_dir / "profile.json").write_text(json.dumps(default_profile(), indent=2, sort_keys=True) + "\n")
    core = profiles_dir() / "angiosperm-core-v1"
    core.mkdir(parents=True, exist_ok=True)
    (core / "README.md").write_text(
        "Species-neutral angiosperm schema: ploidy rules, switchable mechanisms, no calibrated loci.\n"
    )


if __name__ == "__main__":
    dump()
    print("wrote", schemas_dir(), "and", profiles_dir())
