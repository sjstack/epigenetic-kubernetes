from __future__ import annotations

import json
from hashlib import sha256
from typing import Any


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=_default)


def _default(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"not json serializable: {type(obj)!r}")


def digest_bytes(obj: Any) -> str:
    return sha256(canonical_dumps(obj).encode("utf-8")).hexdigest()
