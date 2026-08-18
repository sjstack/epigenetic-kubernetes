"""Docs contract: evidence labels, citations, relative links, example schemas."""

from __future__ import annotations

import json
import re

import jsonschema

from epik.paths import repo_root, schemas_dir
from epik.schema_dump import dump

ROOT = repo_root()
BIO = ROOT / "docs" / "biology"


def test_mechanisms_have_evidence_and_citation():
    rows = json.loads((BIO / "mechanisms.json").read_text())
    assert rows
    for row in rows:
        assert row["evidence"] in {"A", "B", "C", "H"}
        assert row["status"] in {"direct", "coarse-grained", "deferred"}
        assert row["citation"].startswith("https://")
        assert row["id"]


def test_markdown_relative_links_exist():
    missing = []
    for path in (ROOT / "docs").rglob("*.md"):
        text = path.read_text()
        for rel in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if rel.startswith("http") or rel.startswith("#"):
                continue
            target = (path.parent / rel).resolve()
            if not target.exists():
                missing.append((str(path), rel))
    assert missing == []


def test_readme_is_gehring_aligned():
    text = (ROOT / "README.md").read_text()
    assert "Gehring" in text
    assert "arabidopsis-gehring-v1" in text or "Col-0" in text


def test_example_schemas_validate():
    dump()
    tape_schema = json.loads((schemas_dir() / "epik.exposure-tape.v1.json").read_text())
    cross_schema = json.loads((schemas_dir() / "epik.cross.v1.json").read_text())
    tape = json.loads((BIO / "examples" / "exposure-tape.json").read_text())
    cross = json.loads((BIO / "examples" / "cross.json").read_text())
    jsonschema.validate(tape, tape_schema)
    jsonschema.validate(cross, cross_schema)
