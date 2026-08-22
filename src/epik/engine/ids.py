from __future__ import annotations


class IdFactory:
    """Stable causal identifiers derived from a monotonic counter."""

    def __init__(self, start: int = 0) -> None:
        self.n = start

    def new(self, prefix: str) -> str:
        self.n += 1
        return f"{prefix}-{self.n:08d}"
