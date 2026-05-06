from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResponse:
    raw_response: dict
    input_tokens: int
    output_tokens: int


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        raise NotImplementedError

    @abstractmethod
    def supports_structured_output(self) -> bool:
        raise NotImplementedError
