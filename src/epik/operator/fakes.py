"""In-process fakes for operator tests (focused replacement of the legacy mock client)."""

from __future__ import annotations

from typing import Any


class FakeObject:
    def __init__(self, spec: dict[str, Any]) -> None:
        self.spec = spec
        self.status = {"phase": "Pending"}


class FakeCluster:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], FakeObject] = {}
        self.jobs: dict[str, dict[str, Any]] = {}

    def apply(self, kind: str, name: str, spec: dict[str, Any]) -> FakeObject:
        obj = FakeObject(spec)
        self.objects[(kind, name)] = obj
        return obj

    def get(self, kind: str, name: str) -> FakeObject | None:
        return self.objects.get((kind, name))
