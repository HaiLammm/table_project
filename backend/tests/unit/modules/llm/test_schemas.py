
from src.app.llm.schemas import EnrichmentResult, SingleEnrichmentRequest


class TestEnrichmentSchemas:
    def test_enrichment_result_defaults(self):
        result = EnrichmentResult(term="test", language="en", definition="A test definition")

        assert result.source == "llm"
        assert result.validated_against_jmdict is False
        assert result.examples == []
        assert result.related_terms == []
        assert result.ipa is None
        assert result.cefr_level is None
        assert result.jlpt_level is None

    def test_enrichment_result_jp_with_jmdict_validation(self):
        result = EnrichmentResult(
            term="test",
            language="jp",
            definition="A test definition",
            jlpt_level=3,
            validated_against_jmdict=True,
        )

        assert result.language == "jp"
        assert result.jlpt_level == 3
        assert result.validated_against_jmdict is True

    def test_single_enrichment_request_defaults(self):
        request = SingleEnrichmentRequest(term="test", language="en", level="B2")

        assert request.user_id is None

    def test_single_enrichment_request_with_user_id(self):
        request = SingleEnrichmentRequest(term="test", language="en", level="B2", user_id=42)

        assert request.user_id == 42
