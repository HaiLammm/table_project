from dataclasses import dataclass

from src.app.modules.dictionary.application.services import JMdictService


@dataclass(slots=True)
class FakeSense:
    gloss: list[str]


class FakeEntry:
    def __init__(self, text: str, *glosses: str) -> None:
        self._text = text
        self.senses = [FakeSense(list(glosses))]

    def text(self) -> str:
        return self._text


class FakeLookupResult:
    def __init__(self, entries: list[FakeEntry]) -> None:
        self.entries = entries


class FakeDictionary:
    def __init__(self) -> None:
        self.lookup_calls = 0

    def lookup(self, term: str) -> FakeLookupResult:
        self.lookup_calls += 1
        if term == "protocol":
            return FakeLookupResult([FakeEntry("きやく (規約)", "agreement", "protocol")])
        return FakeLookupResult([])


def test_jmdict_lookup_uses_lru_cache() -> None:
    fake_dictionary = FakeDictionary()
    service = JMdictService(dictionary_factory=lambda: fake_dictionary)

    first_result = service.lookup("protocol")
    second_result = service.lookup("protocol")

    assert fake_dictionary.lookup_calls == 1
    assert first_result == second_result
    assert first_result[0].headword == "きやく (規約)"
    assert first_result[0].glosses == ("agreement", "protocol")


def test_jmdict_definition_validation_matches_gloss_text() -> None:
    service = JMdictService(dictionary_factory=FakeDictionary)

    assert service.is_definition_valid("protocol", "Agreement or protocol used by a team") is True
    assert service.is_definition_valid("protocol", "Completely unrelated definition") is False
