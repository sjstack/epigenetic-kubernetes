"""Injectable clocks for deterministic legacy-controller tests."""

from __future__ import annotations


class FakeClock:
    """Monotonic clock that never sleeps; `sleep` advances logical time."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def sleep(self, seconds: float) -> None:
        self.advance(seconds)
