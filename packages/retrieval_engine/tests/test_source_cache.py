from __future__ import annotations

from retrieval_engine.indexing import SourceCache, SourceState, hash_text


def test_source_cache_diff_tracks_added_changed_deleted_and_unchanged() -> None:
    cache = SourceCache(
        {
            "deleted.md": "old-digest",
            "changed.md": "old-digest",
            "same.md": "same-digest",
        }
    )

    current = {
        "changed.md": "new-digest",
        "same.md": "same-digest",
        "added.md": "added-digest",
    }

    diff = cache.diff(current)

    assert diff.added == ["added.md"]
    assert diff.changed == ["changed.md"]
    assert diff.deleted == ["deleted.md"]
    assert diff.unchanged == ["same.md"]
    assert diff.to_process == ["added.md", "changed.md"]
    assert diff.to_remove == ["deleted.md", "changed.md"]
    assert diff.has_changes is True


def test_source_cache_save_and_load_roundtrip(tmp_path) -> None:
    cache_path = tmp_path / "sources.json"
    cache = SourceCache(
        {
            "demo.md": SourceState(
                source="demo.md",
                digest=hash_text("hello"),
                metadata={"path": "docs/demo.md"},
            )
        }
    )

    cache.save(cache_path)
    loaded = SourceCache.load(cache_path)

    assert loaded.states["demo.md"].source == "demo.md"
    assert loaded.states["demo.md"].digest == hash_text("hello")
    assert loaded.states["demo.md"].metadata == {"path": "docs/demo.md"}


def test_source_cache_load_missing_file_returns_empty_cache(tmp_path) -> None:
    cache = SourceCache.load(tmp_path / "missing.json")

    assert cache.states == {}
