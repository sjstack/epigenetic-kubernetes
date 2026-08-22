from __future__ import annotations

from epik.cli import build_parser


def test_cli_has_required_subcommands():
    parser = build_parser()
    names = set(parser._subparsers._group_actions[0].choices)
    for cmd in (
        "simulate",
        "replay",
        "digest",
        "validate-profile",
        "init-cross",
        "run-cross",
        "run-scenario",
        "call-imprinting",
        "run-protocol",
        "export",
        "follow",
        "adapt",
        "record-tape",
        "release-gates",
    ):
        assert cmd in names
