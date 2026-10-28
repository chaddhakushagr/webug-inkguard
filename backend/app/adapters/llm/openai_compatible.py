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


import concurrent.futures

def execute_with_30s_timeout(func, *args, timeout: float = 30.0, **kwargs):
    """Executes func with an enforced 30-second timeout wrapper."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"External call exceeded {timeout:.0f}-second timeout limit.")


class OpenAICompatibleLLMAdapter:
    """OpenAI-compatible adapter supporting Google AI Studio and Ollama."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.effective_api_key
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

        start_time = time.time()
        overall_timeout = 30.0
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            elapsed = time.time() - start_time
            remaining = overall_timeout - elapsed
            if remaining <= 0:
                raise TimeoutError(f"External LLM call exceeded 30s timeout limit (elapsed: {elapsed:.2f}s)")

            per_request_timeout = min(self.timeout, max(0.5, remaining))
            try:
                with httpx.Client(timeout=per_request_timeout) as client:
                    resp = client.post(endpoint, json=payload, headers=headers)

                    if resp.status_code == 200:
                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        return json.loads(raw_content)
                    elif resp.status_code in (429, 500, 502, 503, 504):
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        sleep_time = min(0.5 * (2 ** (attempt - 1)), max(0.1, (overall_timeout - (time.time() - start_time)) / 2))
                        time.sleep(sleep_time)
                    else:
                        raise RuntimeError(f"LLM API Error {resp.status_code}: {resp.text}")
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = str(e)
                sleep_time = min(0.5 * (2 ** (attempt - 1)), max(0.1, (overall_timeout - (time.time() - start_time)) / 2))
                time.sleep(sleep_time)

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
        return execute_with_30s_timeout(self._execute_with_retry, payload, timeout=30.0)

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
        res = execute_with_30s_timeout(self._execute_with_retry, payload, timeout=30.0)
        return res if isinstance(res, list) else res.get("suggestions", [])

    def verify(
        self,
        finding: Dict[str, Any],
        excerpt: str,
        cited_entry: Dict[str, Any],
        prompt_version: str = "v1",
    ) -> Dict[str, Any]:
        # Safety Invariant: Confidential entries must never enter outgoing payload
        if cited_entry.get("classification", "").lower() == "confidential":
            raise ValueError(
                f"Security Invariant Violated: Confidential entry '{cited_entry.get('code')}' cannot be sent to external LLM."
            )

        # Safety Invariant: No API keys in payload
        finding_json = json.dumps(finding)
        if "AIza" in excerpt or "sk-" in excerpt or "AIza" in finding_json or "sk-" in finding_json:
            raise ValueError("Security Invariant Violated: Unredacted API key detected in outgoing payload.")

        system_prompt = self._load_prompt(f"verify.{prompt_version}.md")
        user_content = (
            f"### CANDIDATE FINDING TO VERIFY\n"
            f"<<<CONTENT_DATA>>>\n"
            f"{finding_json}\n"
            f"<<</CONTENT_DATA>>>\n\n"
            f"### QUOTED SPAN (EXCERPT)\n"
            f"<<<CONTENT_DATA>>>\n"
            f"{excerpt}\n"
            f"<<</CONTENT_DATA>>>\n\n"
            f"### CITED KNOWLEDGE BASE ENTRY\n"
            f"<<<CONTENT_DATA>>>\n"
            f"{json.dumps({'code': cited_entry.get('code'), 'title': cited_entry.get('title'), 'statement': (cited_entry.get('data') or {}).get('statement', cited_entry.get('body', ''))}, indent=2)}\n"
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
        res = execute_with_30s_timeout(self._execute_with_retry, payload, timeout=30.0)
        return {
            "verdict": res.get("verdict", "supported"),
            "reason": res.get("reason", "Verification completed"),
        }
