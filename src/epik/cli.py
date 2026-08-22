from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from epik.artifacts import load_checkpoint, load_digest, save_run
from epik.engine.toy import run_toy, toy_step
from epik.model.enums import parse_cross
from epik.model.invariants import check_initialized_world
from epik.model.world import init_cross_world, load_profile, validate_profile, write_world
from epik.simulate import run_cross_token, run_protocol_ros1


def _out(path: str | None) -> Path:
    return Path(path or "artifacts/run")


def cmd_simulate(args: argparse.Namespace) -> int:
    engine = run_toy(seed=args.seed, steps=args.steps, n_entities=args.entities)
    save_run(_out(args.out), engine, extra={"mode": "toy", "steps": args.steps})
    print(engine.digest())
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    src = Path(args.run)
    engine = load_checkpoint(src)
    expected = load_digest(src)
    if args.continue_steps:
        for _ in range(args.continue_steps):
            toy_step(engine, n_entities=args.entities)
        save_run(_out(args.out) if args.out else src / "replay", engine, extra={"replay": True})
    got = engine.digest()
    print(got)
    if not args.continue_steps and got != expected:
        print("digest mismatch", file=sys.stderr)
        return 1
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    print(load_digest(args.run))
    return 0


def cmd_validate_profile(args: argparse.Namespace) -> int:
    profile = load_profile(args.path)
    validate_profile(profile)
    if profile.get("id") == "arabidopsis-gehring-v1" and profile.get("species") != "Arabidopsis thaliana":
        raise SystemExit("arabidopsis-gehring-v1 must be Arabidopsis thaliana")
    print(f"ok {profile['id']} loci={len(profile['loci'])}")
    return 0


def cmd_init_cross(args: argparse.Namespace) -> int:
    maternal, paternal = parse_cross(args.cross) if "x" in args.cross.lower() else (args.maternal, args.paternal)
    world = init_cross_world(maternal, paternal)
    check_initialized_world(world)
    out = Path(args.out or "artifacts/init-cross.json")
    write_world(out, world)
    print(out)
    return 0


def cmd_run_cross(args: argparse.Namespace) -> int:
    engine, world = run_cross_token(args.cross, to_dap=args.to_dap, seed=args.seed)
    save_run(_out(args.out), engine, extra={"cross": args.cross, "to_dap": args.to_dap})
    print(engine.digest())
    print(world["cross_id"], "dap", world.get("dap"))
    return 0


def cmd_run_scenario(args: argparse.Namespace) -> int:
    from epik.scenarios import run_named_scenario

    engine, world, report = run_named_scenario(args.name, seed=args.seed)
    save_run(_out(args.out), engine, extra={"scenario": args.name, "report": report})
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def cmd_call_imprinting(args: argparse.Namespace) -> int:
    world = json.loads(Path(args.run, "world.json").read_text())
    calls = world.get("imprinting_calls", {})
    print(json.dumps(calls, indent=2, sort_keys=True))
    return 0


def cmd_run_protocol(args: argparse.Namespace) -> int:
    if args.name != "ros1-homeostasis":
        raise SystemExit(f"unknown protocol {args.name}")
    pert = {}
    if args.sensor_broken:
        pert = {"ros1": False, "ros1_sensor": False}
    if args.selection_only:
        pert = {"selection_only": True}
    engine, world = run_protocol_ros1(seed=args.seed, generations=args.generations, perturbations=pert)
    save_run(_out(args.out), engine, extra={"protocol": args.name})
    print(json.dumps(world.get("trajectory"), indent=2))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    from epik.api.outbound import OutboundAPI

    engine = load_checkpoint(args.run)
    payload = OutboundAPI(engine).export()
    out = Path(args.out or Path(args.run) / "export.json")
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(out)
    return 0


def cmd_follow(args: argparse.Namespace) -> int:
    from epik.api.outbound import OutboundAPI

    engine = load_checkpoint(args.run)
    for event in OutboundAPI(engine).follow():
        print(json.dumps(event, sort_keys=True))
    return 0


def cmd_adapt(args: argparse.Namespace) -> int:
    from epik.integration.adapter import adapt_artifact

    result = adapt_artifact(Path(args.run) / "world.json", out_path=args.out, target_attribute=args.target)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def cmd_record_tape(args: argparse.Namespace) -> int:
    from epik.integration.tape import transcribe_telemetry, validate_tape

    raw = json.loads(Path(args.input).read_text())
    tape = transcribe_telemetry(raw) if args.telemetry else validate_tape(raw)
    Path(args.out).write_text(json.dumps(tape, indent=2, sort_keys=True))
    print(args.out)
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    from epik.release.gates import run_benchmark_suite

    report = run_benchmark_suite(seed=args.seed)
    Path(args.out or "artifacts/benchmark.json").parent.mkdir(parents=True, exist_ok=True)
    Path(args.out or "artifacts/benchmark.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps({"passed": report["passed"], "n": report["n"]}, indent=2))
    return 0 if report["passed"] else 1


def cmd_release_gates(args: argparse.Namespace) -> int:
    from epik.release.gates import run_release_gates

    report = run_release_gates(seed=args.seed)
    print(json.dumps({"passed": report["passed"], "checks": list(report["checks"])}, indent=2))
    return 0 if report["passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="epik")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("simulate")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--steps", type=int, default=10)
    p.add_argument("--entities", type=int, default=4)
    p.add_argument("--out", default="artifacts/toy")
    p.set_defaults(func=cmd_simulate)

    p = sub.add_parser("replay")
    p.add_argument("run")
    p.add_argument("--continue-steps", type=int, default=0)
    p.add_argument("--entities", type=int, default=4)
    p.add_argument("--out")
    p.set_defaults(func=cmd_replay)

    p = sub.add_parser("digest")
    p.add_argument("run")
    p.set_defaults(func=cmd_digest)

    p = sub.add_parser("validate-profile")
    p.add_argument("path", nargs="?", default=None)
    p.set_defaults(func=cmd_validate_profile)

    p = sub.add_parser("init-cross")
    p.add_argument("--cross", default="ColxCvi")
    p.add_argument("--maternal")
    p.add_argument("--paternal")
    p.add_argument("--out")
    p.set_defaults(func=cmd_init_cross)

    p = sub.add_parser("run-cross")
    p.add_argument("cross")
    p.add_argument("--to-dap", type=int, default=7)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", default="artifacts/cross")
    p.set_defaults(func=cmd_run_cross)

    p = sub.add_parser("run-scenario")
    p.add_argument("name")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", default="artifacts/scenario")
    p.set_defaults(func=cmd_run_scenario)

    p = sub.add_parser("call-imprinting")
    p.add_argument("run")
    p.set_defaults(func=cmd_call_imprinting)

    p = sub.add_parser("run-protocol")
    p.add_argument("name")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--generations", type=int, default=5)
    p.add_argument("--sensor-broken", action="store_true")
    p.add_argument("--selection-only", action="store_true")
    p.add_argument("--out", default="artifacts/protocol")
    p.set_defaults(func=cmd_run_protocol)

    p = sub.add_parser("export")
    p.add_argument("run")
    p.add_argument("--out")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("follow")
    p.add_argument("run")
    p.set_defaults(func=cmd_follow)

    p = sub.add_parser("adapt")
    p.add_argument("run")
    p.add_argument("--target", default="spec.replicas")
    p.add_argument("--out")
    p.set_defaults(func=cmd_adapt)

    p = sub.add_parser("record-tape")
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--telemetry", action="store_true")
    p.set_defaults(func=cmd_record_tape)

    p = sub.add_parser("benchmark")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", default="artifacts/benchmark.json")
    p.set_defaults(func=cmd_benchmark)

    p = sub.add_parser("release-gates")
    p.add_argument("--seed", type=int, default=1)
    p.set_defaults(func=cmd_release_gates)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
