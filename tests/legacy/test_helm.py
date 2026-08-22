"""Helm chart contract: lowercase count and labels aligned with the mock client."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHART = ROOT / "charts" / "population"
TEMPLATE = CHART / "templates" / "organism.yaml"
VALUES = CHART / "values.yaml"


def test_count_key_is_lowercase():
    values = VALUES.read_text()
    template = TEMPLATE.read_text()
    assert "count: 5" in values
    assert "Count:" not in values
    assert ".Values.count" in template
    assert ".Values.Count" not in template


def test_mock_aligned_labels():
    text = TEMPLATE.read_text()
    assert "strategy: clonal" in text
    assert "strategy: transgenerational" in text
    assert "lineage: {{ printf \"organism-%d\" $i | quote }}" in text


def test_helm_template_output_is_stable():
    if shutil.which("helm") is None:
        pytest_skip = __import__("pytest").skip
        pytest_skip("helm not installed")
    cmd = [
        "helm",
        "template",
        "population",
        str(CHART),
        "--set",
        "strategy=clonal",
        "--set",
        "count=2",
    ]
    first = subprocess.check_output(cmd, text=True)
    second = subprocess.check_output(cmd, text=True)
    assert first == second
    digest = hashlib.sha256(first.encode()).hexdigest()
    assert "strategy: clonal" in first
    assert digest == hashlib.sha256(second.encode()).hexdigest()
