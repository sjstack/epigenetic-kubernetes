from __future__ import annotations

from typing import Any

from epik.canonical import canonical_dumps
from epik.engine.clock import LogicalClock
from epik.engine.digest import combined_digest, event_digest, state_digest
from epik.engine.ids import IdFactory
from epik.engine.intents import Event, Intent
from epik.engine.ledger import Ledger
from epik.engine.reducer import default_reducer
from epik.engine.rng import StreamRng


class Engine:
    def __init__(self, seed: int = 1, state: dict[str, Any] | None = None) -> None:
        self.seed = int(seed)
        self.clock = LogicalClock()
        self.ids = IdFactory()
        self.rng = StreamRng(self.seed)
        self.ledger = Ledger()
        self.reducer = default_reducer()
        self.state: dict[str, Any] = state if state is not None else empty_state(self.seed)
        self._pending: list[Intent] = []
        self.subscribers: list[Any] = []

    def subscribe(self, callback) -> None:
        """Read-only outbound hook. Callbacks must not mutate engine state."""
        self.subscribers.append(callback)

    def propose(self, intent: Intent) -> None:
        self._pending.append(intent)

    def commit_pending(self) -> list[Event]:
        ordered = sorted(self._pending, key=lambda i: i.sort_key())
        self._pending.clear()
        return [self._commit(intent) for intent in ordered]

    def commit(self, intent: Intent) -> Event:
        return self._commit(intent)

    def _commit(self, intent: Intent) -> Event:
        stream_key = "|".join(
            map(str, (intent.mechanism, intent.entity_id, intent.kind, self.clock.t, intent.sort_key()[-1]))
        )
        rng = self.rng.stream("commit", stream_key)
        payload = self.reducer.apply(self.state, intent, rng)
        event = Event(
            index=len(self.ledger.events),
            logical_time=self.clock.t,
            kind=intent.kind,
            mechanism=intent.mechanism,
            entity_id=intent.entity_id,
            payload=payload,
            rng_stream=stream_key,
            parent_index=len(self.ledger.events) - 1 if self.ledger.events else None,
        )
        self.ledger.append(event)
        self.clock.advance()
        for cb in self.subscribers:
            cb(event)
        return event

    def digest(self) -> str:
        return combined_digest(self.state, self.ledger)

    def state_digest(self) -> str:
        return state_digest(self.state)

    def event_digest(self) -> str:
        return event_digest(self.ledger)

    def checkpoint(self) -> dict[str, Any]:
        return {
            "schema": "epik.checkpoint.v1",
            "seed": self.seed,
            "clock": self.clock.t,
            "id_counter": self.ids.n,
            "state": self.state,
            "events": self.ledger.to_list(),
        }

    @classmethod
    def restore(cls, payload: dict[str, Any]) -> Engine:
        engine = cls(seed=payload["seed"], state=payload["state"])
        engine.clock.t = payload["clock"]
        engine.ids.n = payload["id_counter"]
        engine.ledger = Ledger.from_list(payload["events"])
        return engine

    def replay(self) -> Engine:
        """Rebuild state by re-applying ledger events on a fresh engine (toy/set_path/merge)."""
        clone = Engine(seed=self.seed)
        for event in self.ledger.events:
            intent = Intent(
                kind=event.kind,
                mechanism=event.mechanism,
                entity_id=event.entity_id,
                payload=_replay_payload(event),
                logical_time=event.logical_time,
            )
            clone.commit(intent)
        return clone


def empty_state(seed: int) -> dict[str, Any]:
    return {
        "schema": "epik.world.v1",
        "seed": seed,
        "entities": {},
        "meta": {},
        "world": {},
    }


def _replay_payload(event: Event) -> dict[str, Any]:
    if event.kind == "replace_state":
        return event.payload if "state" in event.payload else {"state": event.payload}
    if event.kind == "set_path":
        return {"path": event.payload["path"], "value": event.payload["value"]}
    if event.kind == "merge_entity":
        return {"patch": event.payload.get("patch", event.payload)}
    return dict(event.payload)


def dump_run(engine: Engine) -> dict[str, Any]:
    return {
        "schema": "epik.run.v1",
        "seed": engine.seed,
        "digest": engine.digest(),
        "state_digest": engine.state_digest(),
        "event_digest": engine.event_digest(),
        "checkpoint": engine.checkpoint(),
        "canonical": canonical_dumps({"state": engine.state, "events": engine.ledger.to_list()}),
    }
