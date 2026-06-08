from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceState:
    source: str
    digest: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SourceDiff:
    added: list[str]
    changed: list[str]
    deleted: list[str]
    unchanged: list[str]

    @property
    def to_process(self) -> list[str]:
        return [*self.added, *self.changed]

    @property
    def to_remove(self) -> list[str]:
        return [*self.deleted, *self.changed]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.changed or self.deleted)


class SourceCache:
    """用于宿主项目增量构建的小型 source 摘要缓存。"""

    def __init__(self, states: Mapping[str, SourceState | str] | None = None) -> None:
        self.states: dict[str, SourceState] = {}
        for source, state in (states or {}).items():
            self.states[source] = _coerce_source_state(source, state)

    @classmethod
    def load(cls, path: str | Path) -> SourceCache:
        cache_path = Path(path)
        if not cache_path.exists():
            return cls()

        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("source cache payload must be a JSON object.")

        raw_states = payload.get("sources", payload)
        if not isinstance(raw_states, dict):
            raise ValueError("source cache sources must be a JSON object.")

        states: dict[str, SourceState] = {}
        for source, value in raw_states.items():
            if isinstance(value, str):
                states[source] = SourceState(source=source, digest=value)
            elif isinstance(value, dict):
                digest = str(value.get("digest", value.get("hash", "")))
                metadata = value.get("metadata", {})
                states[source] = SourceState(
                    source=source,
                    digest=digest,
                    metadata={str(key): str(item) for key, item in metadata.items()}
                    if isinstance(metadata, dict)
                    else {},
                )
        return cls(states)

    def save(self, path: str | Path) -> None:
        cache_path = Path(path)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
        payload = {
            "sources": {
                source: {
                    "digest": state.digest,
                    "metadata": state.metadata,
                }
                for source, state in sorted(self.states.items())
            }
        }
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(cache_path)

    def diff(self, current: Mapping[str, SourceState | str]) -> SourceDiff:
        current_states = {
            source: _coerce_source_state(source, state) for source, state in current.items()
        }
        old_sources = set(self.states)
        current_sources = set(current_states)

        added = sorted(current_sources - old_sources)
        deleted = sorted(old_sources - current_sources)
        changed = sorted(
            source
            for source in old_sources.intersection(current_sources)
            if self.states[source].digest != current_states[source].digest
        )
        unchanged = sorted(
            source
            for source in old_sources.intersection(current_sources)
            if self.states[source].digest == current_states[source].digest
        )
        return SourceDiff(
            added=added,
            changed=changed,
            deleted=deleted,
            unchanged=unchanged,
        )

    def replace(self, states: Mapping[str, SourceState | str]) -> None:
        self.states = {
            source: _coerce_source_state(source, state) for source, state in states.items()
        }

    def update(self, states: Mapping[str, SourceState | str]) -> None:
        for source, state in states.items():
            self.states[source] = _coerce_source_state(source, state)

    def remove(self, sources: Iterable[str]) -> None:
        for source in sources:
            self.states.pop(source, None)


def hash_text(text: str, *, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def hash_file(path: str | Path, *, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_file_state(
    paths: Iterable[str | Path],
    *,
    source_id: str = "name",
    algorithm: str = "sha256",
) -> dict[str, SourceState]:
    states: dict[str, SourceState] = {}
    for raw_path in paths:
        path = Path(raw_path)
        if source_id == "name":
            source = path.name
        elif source_id == "path":
            source = str(path)
        else:
            raise ValueError("source_id must be 'name' or 'path'.")

        states[source] = SourceState(
            source=source,
            digest=hash_file(path, algorithm=algorithm),
            metadata={"path": str(path)},
        )
    return states


def _coerce_source_state(source: str, state: SourceState | str) -> SourceState:
    if isinstance(state, SourceState):
        return state
    return SourceState(source=source, digest=str(state))
