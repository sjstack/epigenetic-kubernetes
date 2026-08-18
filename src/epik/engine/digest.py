from __future__ import annotations

from typing import Any

from epik.canonical import digest_bytes
from epik.engine.ledger import Ledger


def combined_digest(state: dict[str, Any], ledger: Ledger) -> str:
    return digest_bytes({"state": state, "events": ledger.to_list()})


def state_digest(state: dict[str, Any]) -> str:
    return digest_bytes(state)


def event_digest(ledger: Ledger) -> str:
    return digest_bytes(ledger.to_list())
