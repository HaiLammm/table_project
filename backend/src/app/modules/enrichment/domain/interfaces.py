from abc import ABC, abstractmethod

from src.app.modules.enrichment.domain.entities import EnrichedTerm


class EnrichmentServiceInterface(ABC):
    @abstractmethod
    async def find_terms_for_request(
        self, topic: str, language: str, level: str, count: int
    ) -> list[EnrichedTerm]:
        raise NotImplementedError
