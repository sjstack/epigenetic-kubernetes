from __future__ import annotations


class LogicalClock:
    """Integer logical time. Wall-clock is never consulted."""

    def __init__(self, start: int = 0) -> None:
        self.t = start

    def advance(self, n: int = 1) -> int:
        self.t += n
        return self.t
