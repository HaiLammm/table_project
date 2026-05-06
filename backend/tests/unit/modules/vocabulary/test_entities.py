from datetime import UTC, datetime

from src.app.modules.vocabulary.domain.entities import VocabularyDefinition, VocabularyTerm


def test_vocabulary_term_keeps_hierarchy_and_definitions() -> None:
    now = datetime.now(UTC)
    definition = VocabularyDefinition(
        language="en",
        definition="A set of rules that govern communication.",
        ipa="/ˈprəʊ.tə.kɒl/",
        examples=["HTTP is a web protocol."],
        source="seed",
        validated_against_jmdict=False,
    )

    term = VocabularyTerm(
        term="protocol",
        language="en",
        parent_id=7,
        cefr_level="B2",
        part_of_speech="noun",
        definitions=[definition],
        created_at=now,
        updated_at=now,
    )

    assert term.id is None
    assert term.parent_id == 7
    assert term.definitions == [definition]
    assert term.created_at == now
    assert term.updated_at == now


def test_vocabulary_definition_defaults_examples_and_validation_flag() -> None:
    definition = VocabularyDefinition(
        language="jp",
        definition="猫",
        source="seed",
    )

    assert definition.id is None
    assert definition.term_id is None
    assert definition.examples == []
    assert definition.validated_against_jmdict is False
