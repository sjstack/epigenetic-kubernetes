from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from epik.engine.engine import Engine
from epik.operator.reconcile import Operator, run_spec
from epik.simulate import continue_cross, run_cross_token


def test_duplicate_reconcile_no_duplicate_biology(tmp_path):
    op = Operator(tmp_path)
    spec = {"name": "r1", "seed": 3, "cross": "ColxCvi", "to_dap": 3}
    a = op.reconcile(spec)
    b = op.reconcile(spec)
    assert a["digest"] == b["digest"]
    assert a["key"] == b["key"]


def test_local_and_subprocess_job_parity(tmp_path):
    spec = {"name": "job", "seed": 4, "cross": "ColxLer", "to_dap": 3}
    local_dir = tmp_path / "local"
    run_spec(spec, local_dir)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    job_dir = tmp_path / "job"
    subprocess.check_call(
        [sys.executable, "-m", "epik.operator.job", "--spec", str(spec_path), "--out", str(job_dir)],
        cwd=str(Path(__file__).resolve().parents[2]),
    )
    assert (local_dir / "digest.txt").read_text() == (job_dir / "digest.txt").read_text()


def test_mid_run_resume_matches_full(tmp_path):
    full_e, _ = run_cross_token("ColxCvi", seed=5, to_dap=7)
    mid_e, _ = run_cross_token("ColxCvi", seed=5, to_dap=3)
    restored = Engine.restore(mid_e.checkpoint())
    continue_cross(restored, to_dap=7)
    assert restored.digest() == full_e.digest()
