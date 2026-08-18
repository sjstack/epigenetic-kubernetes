from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Intent:
    kind: str
    mechanism: str
    entity_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    logical_time: int = 0

    def sort_key(self) -> tuple:
        from epik.canonical import canonical_dumps

        return (
            self.logical_time,
            self.mechanism,
            self.entity_id,
            self.kind,
            canonical_dumps(self.payload),
        )


@dataclass
class Event:
    index: int
    logical_time: int
    kind: str
    mechanism: str
    entity_id: str
    payload: dict[str, Any]
    rng_stream: str
    parent_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "logical_time": self.logical_time,
            "kind": self.kind,
            "mechanism": self.mechanism,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "rng_stream": self.rng_stream,
            "parent_index": self.parent_index,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        return cls(**data)
