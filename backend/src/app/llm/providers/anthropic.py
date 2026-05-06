import json
from typing import Any

import httpx

from src.app.core.config import settings
from src.app.llm.providers import LLMProvider, ProviderResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.anthropic_model
        self._base_url = "https://api.anthropic.com/v1/messages"

    def supports_structured_output(self) -> bool:
        return False

    async def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required")

        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": self._model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            }
            headers = {
                "content-type": "application/json",
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
            }
            response = await client.post(self._base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content_blocks = data.get("content", [])
        text = next(
            (block.get("text", "") for block in content_blocks if block.get("type") == "text"),
            "",
        )

        input_tokens = data.get("usage", {}).get("input_tokens", 0)
        output_tokens = data.get("usage", {}).get("output_tokens", 0)

        return ProviderResponse(
            raw_response={"text": text, "raw": data},
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def parse_enrichment_response(self, response: ProviderResponse) -> dict[str, Any]:
        try:
            raw_text = response.raw_response.get("text", "")
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response"}
