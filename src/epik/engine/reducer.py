from __future__ import annotations

from typing import Any

from epik.engine.intents import Intent

Handler = Any


class Reducer:
    """Single writer: every committed intent becomes one event."""

    def __init__(self) -> None:
        self.handlers: dict[str, Handler] = {}

    def register(self, kind: str, handler: Handler) -> None:
        self.handlers[kind] = handler

    def apply(self, state: dict[str, Any], intent: Intent, rng) -> dict[str, Any]:
        if intent.kind not in self.handlers:
            raise KeyError(f"no reducer for intent kind {intent.kind!r}")
        payload = self.handlers[intent.kind](state, intent, rng)
        return payload if payload is not None else dict(intent.payload)


def default_reducer() -> Reducer:
    reducer = Reducer()
    reducer.register("flip", _flip)
    reducer.register("set_path", _set_path)
    reducer.register("merge_entity", _merge_entity)
    reducer.register("replace_state", _replace_state)
    reducer.register("noop", lambda state, intent, rng: dict(intent.payload))
    reducer.register("set_world", _set_world)
    return reducer


def _flip(state: dict[str, Any], intent: Intent, rng) -> dict[str, Any]:
    entities = state.setdefault("entities", {})
    ent = entities.setdefault(intent.entity_id, {"kind": "flipper", "value": 0})
    ent["value"] = 1 - int(ent.get("value", 0))
    return {"value": ent["value"]}


def _set_path(state: dict[str, Any], intent: Intent, rng) -> dict[str, Any]:
    path = list(intent.payload["path"])
    value = intent.payload["value"]
    cursor = state
    for key in path[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[path[-1]] = value
    return {"path": path, "value": value}


def _merge_entity(state: dict[str, Any], intent: Intent, rng) -> dict[str, Any]:
    entities = state.setdefault("entities", {})
    current = entities.get(intent.entity_id, {})
    patch = dict(intent.payload.get("patch", {}))
    merged = {**current, **patch}
    entities[intent.entity_id] = merged
    return {"entity_id": intent.entity_id, "patch": patch}


def _replace_state(state: dict[str, Any], intent: Intent, rng) -> dict[str, Any]:
    incoming = intent.payload["state"]
    state.clear()
    state.update(incoming)
    return {"replaced": True}


def _set_world(state: dict[str, Any], intent: Intent, rng) -> dict[str, Any]:
    world = intent.payload["world"]
    state["world"] = world
    return {"stage": world.get("stage"), "dap": world.get("dap")}
