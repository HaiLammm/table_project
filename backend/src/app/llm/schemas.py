from pydantic import BaseModel, Field


class EnrichmentResult(BaseModel):
    term: str
    language: str
    definition: str
    ipa: str | None = None
    cefr_level: str | None = None
    jlpt_level: int | None = None
    examples: list[str] = Field(default_factory=list)
    related_terms: list[str] = Field(default_factory=list)
    source: str = "llm"
    validated_against_jmdict: bool = False
    candidate_id: str | None = None


class SingleEnrichmentRequest(BaseModel):
    term: str
    language: str
    level: str
    user_id: int | None = None


class BatchEnrichmentRequest(BaseModel):
    terms: list[SingleEnrichmentRequest]
    user_id: int | None = None
