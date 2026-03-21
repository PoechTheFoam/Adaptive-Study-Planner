from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate_json_payload(self, prompt: str) -> dict[str, Any]:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json",
            },
        }
        response = self._post_json(payload)
        text = self._extract_text(response)
        return json.loads(self._strip_code_fences(text))

    def generate_quiz_payload(self, prompt: str) -> dict[str, Any]:
        return self.generate_json_payload(prompt)

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(payload).encode("utf-8")
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{parse.quote(self.model)}:generateContent?key={parse.quote(self.api_key)}"
        )
        req = request.Request(
            endpoint,
            data=encoded,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API HTTP error: {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Gemini API connection error: {exc}") from exc

    def _extract_text(self, response: dict[str, Any]) -> str:
        candidates = response.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")

        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [part.get("text", "") for part in parts if part.get("text")]
        if not texts:
            raise RuntimeError("Gemini returned an empty text payload.")
        return "\n".join(texts)

    def _strip_code_fences(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3:
                return "\n".join(lines[1:-1]).strip()
        return stripped
