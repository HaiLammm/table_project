import json
from typing import Any

import httpx

from src.app.core.config import settings
from src.app.llm.providers import LLMProvider, ProviderResponse


class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or settings.deepseek_api_key
        self._model = model or settings.deepseek_model
        self._base_url = "https://api.deepseek.com/v1/chat/completions"

    def supports_structured_output(self) -> bool:
        return True

    async def complete(self, prompt: str, **kwargs: object) -> ProviderResponse:
        if not self._api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is required")

        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
            }
            headers = {
                "content-type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            }
            response = await client.post(self._base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        text = choices[0].get("message", {}).get("content", "") if choices else ""

        return ProviderResponse(
            raw_response={"text": text, "raw": data},
            input_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            output_tokens=data.get("usage", {}).get("completion_tokens", 0),
        )

    def parse_enrichment_response(self, response: ProviderResponse) -> dict[str, Any]:
        try:
            raw_text = response.raw_response.get("text", "")
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response"}
