from datetime import UTC, datetime

from src.app.modules.collections.domain.entities import Collection, CollectionTerm


def test_collection_entity_keeps_progress_fields() -> None:
    now = datetime.now(UTC)

    collection = Collection(
        id=1,
        user_id=7,
        name="Networking",
        icon="🌍",
        term_count=12,
        mastery_percent=58,
        created_at=now,
        updated_at=now,
    )

    assert collection.id == 1
    assert collection.term_count == 12
    assert collection.mastery_percent == 58
    assert collection.created_at == now
    assert collection.updated_at == now


def test_collection_term_entity_defaults_added_at() -> None:
    collection_term = CollectionTerm(collection_id=3, term_id=9)

    assert collection_term.id is None
    assert collection_term.added_at is None
