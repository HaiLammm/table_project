import json
from typing import Any

import httpx

from src.app.core.config import settings
from src.app.llm.providers import LLMProvider, ProviderResponse


class GoogleProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or settings.google_api_key
        self._model = model or settings.google_model
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def supports_structured_output(self) -> bool:
        return True

    async def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        if not self._api_key:
            raise RuntimeError("GOOGLE_API_KEY is required")

        async with httpx.AsyncClient(timeout=60.0) as client:
            url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                },
            }
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                text = parts[0].get("text", "")

        return ProviderResponse(
            raw_response={"text": text, "raw": data},
            input_tokens=data.get("usageMetadata", {}).get("promptTokenCount", 0),
            output_tokens=data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
        )

    def parse_enrichment_response(self, response: ProviderResponse) -> dict[str, Any]:
        try:
            raw_text = response.raw_response.get("text", "")
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response"}
