from __future__ import annotations

from epik.engine.intents import Event


class Ledger:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def append(self, event: Event) -> Event:
        self.events.append(event)
        return event

    def to_list(self) -> list[dict]:
        return [e.to_dict() for e in self.events]

    @classmethod
    def from_list(cls, rows: list[dict]) -> Ledger:
        ledger = cls()
        ledger.events = [Event.from_dict(r) for r in rows]
        return ledger
