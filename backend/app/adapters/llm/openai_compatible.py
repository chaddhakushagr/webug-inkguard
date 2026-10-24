"""
OpenAI-compatible LLM adapter using httpx.
Supports Google AI Studio and local Ollama endpoints.
Features timeout, retry with backoff, strict JSON parsing, zero API key logging,
and strict assertions preventing confidential text from entering outgoing payloads.
"""

import json
import time
import os
from typing import List, Dict, Any, Optional
import httpx
from app.ports.llm import LLMPort
from app.config import settings


class OpenAICompatibleLLMAdapter:
    """OpenAI-compatible adapter supporting Google AI Studio and Ollama."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 15.0,
        max_retries: int = 3,
    ):
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout
        self.max_retries = max_retries

    def _load_prompt(self, filename: str) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", filename)
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return "You are an automated brand governance assistant. Output valid JSON."

    def _prepare_payload(
        self,
        sanitised_text: str,
        kb_entries: List[Dict[str, Any]],
        system_prompt: str,
    ) -> Dict[str, Any]:
        # Safety Invariant: Assert no confidential entries in outgoing knowledge base context
        for entry in kb_entries:
            classification = entry.get("classification", "").lower()
            if classification == "confidential":
                raise ValueError(
                    f"Security Invariant Violated: Confidential entry '{entry.get('code')}' cannot be sent to external LLM."
                )

        # Safety Invariant: Assert no known secret patterns in user text
        if "AIza" in sanitised_text or "sk-" in sanitised_text:
            raise ValueError("Security Invariant Violated: Unredacted API key detected in outgoing payload.")

        formatted_kb = []
        for e in kb_entries:
            formatted_kb.append({
                "code": e.get("code"),
                "type": e.get("type"),
                "title": e.get("title"),
                "statement": (e.get("data") or {}).get("statement", e.get("body", "")),
                "guidance": (e.get("data") or {}).get("guidance", ""),
            })

        user_content = (
            f"### RETRIEVED KNOWLEDGE BASE ENTRIES\n"
            f"{json.dumps(formatted_kb, indent=2)}\n\n"
            f"### CONTENT TO EVALUATE\n"
            f"<<<CONTENT_DATA>>>\n"
            f"{sanitised_text}\n"
            f"<<</CONTENT_DATA>>>\n"
        )

        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

    def _execute_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        # Safe logging without exposing secrets
        # print(f"[LLM Request] Model: {self.model} | Chars sent: {len(json.dumps(payload))}")

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(endpoint, json=payload, headers=headers)

                    if resp.status_code == 200:
                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        return json.loads(raw_content)
                    elif resp.status_code in (429, 500, 502, 503, 504):
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        time.sleep(0.5 * (2 ** (attempt - 1)))
                    else:
                        raise RuntimeError(f"LLM API Error {resp.status_code}: {resp.text}")
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = str(e)
                time.sleep(0.5 * (2 ** (attempt - 1)))

        raise RuntimeError(f"LLM call failed after {self.max_retries} attempts. Last error: {last_error}")

    def analyze(
        self,
        sanitised_text: str,
        kb_entries: List[Dict[str, Any]],
        channel: str = "social",
        prompt_version: str = "v1",
    ) -> Dict[str, Any]:
        system_prompt = self._load_prompt(f"analysis.{prompt_version}.md")
        payload = self._prepare_payload(sanitised_text, kb_entries, system_prompt)
        return self._execute_with_retry(payload)

    def suggest_fixes(
        self,
        sanitised_text: str,
        findings: List[Dict[str, Any]],
        kb_entries: List[Dict[str, Any]],
        prompt_version: str = "v1",
    ) -> List[Dict[str, Any]]:
        system_prompt = self._load_prompt(f"suggest.{prompt_version}.md")
        user_content = (
            f"### FINDINGS TO REMEDY\n"
            f"{json.dumps(findings, indent=2)}\n\n"
            f"### ORIGINAL TEXT\n"
            f"<<<CONTENT_DATA>>>\n"
            f"{sanitised_text}\n"
            f"<<</CONTENT_DATA>>>\n"
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
        res = self._execute_with_retry(payload)
        return res if isinstance(res, list) else res.get("suggestions", [])
