from __future__ import annotations

import argparse
import json
from pathlib import Path

from epik.operator.reconcile import run_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="epik-operator-job")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    spec = json.loads(Path(args.spec).read_text())
    result = run_spec(spec, args.out)
    Path(args.out).mkdir(parents=True, exist_ok=True)
    Path(args.out, "job-status.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(result["digest"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
