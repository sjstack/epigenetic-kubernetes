from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence


class StreamRng:
    """Hierarchical counter-based RNG. Streams are independent of draw order across keys."""

    def __init__(self, seed: int) -> None:
        self.seed = int(seed)

    def stream(self, *keys: object) -> random.Random:
        material = f"{self.seed}|" + "|".join(map(str, keys))
        digest = hashlib.sha256(material.encode("utf-8")).digest()
        derived = int.from_bytes(digest[:8], "big")
        return random.Random(derived)

    def keyed(self, keys: Sequence[object]) -> random.Random:
        return self.stream(*keys)
