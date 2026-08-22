from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from epik.artifacts import load_digest, save_run
from epik.simulate import continue_cross, run_cross_token


def run_spec(spec: dict[str, Any], outdir: str | Path) -> dict[str, Any]:
    engine, world = run_cross_token(
        spec["cross"],
        seed=int(spec.get("seed", 1)),
        to_dap=int(spec.get("to_dap", 7)),
        perturbations=spec.get("perturbations"),
    )
    save_run(outdir, engine, extra={"spec": spec, "cross_id": world.get("cross_id")})
    return {"digest": engine.digest(), "status": "Succeeded", "outdir": str(outdir)}


class Operator:
    """Single-writer reconciler. Molecular detail lives in artifacts, not etcd."""

    def __init__(self, artifact_root: str | Path) -> None:
        self.artifact_root = Path(artifact_root)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.runs: dict[str, dict[str, Any]] = {}

    def key(self, spec: dict[str, Any]) -> str:
        return f"{spec['name']}:{spec.get('seed', 1)}:{spec['cross']}:{spec.get('to_dap', 7)}"

    def reconcile(self, spec: dict[str, Any]) -> dict[str, Any]:
        key = self.key(spec)
        existing = self.runs.get(key)
        if existing and existing.get("status") == "Succeeded":
            return existing
        outdir = self.artifact_root / spec["name"]
        if spec.get("resume") and (outdir / "checkpoint.json").exists():
            from epik.artifacts import load_checkpoint

            engine = load_checkpoint(outdir)
            engine, world = continue_cross(engine, to_dap=int(spec.get("to_dap", 7)))
            save_run(outdir, engine, extra={"spec": spec, "resumed": True})
            result = {"digest": engine.digest(), "status": "Succeeded", "outdir": str(outdir), "key": key}
            self.runs[key] = result
            return result
        result = run_spec(spec, outdir)
        result["key"] = key
        self.runs[key] = result
        return result

    def status(self, name: str) -> dict[str, Any] | None:
        for key, row in self.runs.items():
            if key.startswith(name + ":"):
                return row
        path = self.artifact_root / name
        if (path / "digest.txt").exists():
            return {"digest": load_digest(path), "status": "Succeeded", "outdir": str(path)}
        return None


class QueryHandler(BaseHTTPRequestHandler):
    operator: Operator

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/health", "/healthz"}:
            self._send(200, {"ok": True})
            return
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "runs":
            name = parts[1]
            row = self.operator.status(name)
            if not row:
                self._send(404, {"error": "not found"})
                return
            if len(parts) == 3 and parts[2] == "digest":
                self._send(200, {"digest": row["digest"]})
                return
            self._send(200, row)
            return
        self._send(404, {"error": "not found"})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(operator: Operator, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    QueryHandler.operator = operator
    server = ThreadingHTTPServer((host, port), QueryHandler)
    return server
