"""
Pure domain sanitisation stage.
Detects prompt injection phrases and redacts sensitive PII / secrets.
Stores placeholder map in memory; logs only type and count.
"""

import re
from typing import Dict
from app.domain.review.models import ReviewContext, ReviewStage

INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions\b",
    r"(?i)\bdisregard\s+(all\s+)?(prior|previous)\s+rules\b",
    r"(?i)\bsystem\s+override\b",
    r"(?i)\byou\s+are\s+now\s+(a|an)?\b",
    r"(?i)\boutput\s+json\s+with\s+claims\s*=\s*\[\s*\]\b",
    r"(?i)\bdo\s+not\s+report\s+any\s+(findings|issues)\b",
    r"(?i)\b<!--\s*system\s+override\b",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
SECRET_PATTERN = re.compile(
    r"\b(?:sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z-_]{28,45}|ghp_[a-zA-Z0-9]{36}|AKIA[0-9A-Z]{16}|ey[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,})\b"
)
CONFIDENTIAL_TERMS = ["Project Lumina", "Lumina Dew", "November 15, 2026", "secret key"]


class SanitiseStage:
    name: str = "Sanitise"

    def process(self, context: ReviewContext) -> ReviewContext:
        text = context.text
        flags = list(context.flags)
        placeholder_map: Dict[str, str] = {}
        redaction_counts = {"emails": 0, "phones": 0, "api_keys": 0, "secrets": 0}

        # 1. Detect prompt injection
        for pat in INJECTION_PATTERNS:
            if re.search(pat, text):
                if "prompt_injection_flagged" not in flags:
                    flags.append("prompt_injection_flagged")
                break

        sanitised = text

        # 2. Redact secrets & API keys
        def redact_secret(match):
            nonlocal redaction_counts
            redaction_counts["api_keys"] += 1
            idx = redaction_counts["api_keys"]
            token = f"[API_KEY_REDACTED_{idx}]"
            placeholder_map[token] = match.group(0)
            return token

        sanitised = SECRET_PATTERN.sub(redact_secret, sanitised)

        # 3. Redact emails
        def redact_email(match):
            nonlocal redaction_counts
            redaction_counts["emails"] += 1
            idx = redaction_counts["emails"]
            token = f"[EMAIL_REDACTED_{idx}]"
            placeholder_map[token] = match.group(0)
            return token

        sanitised = EMAIL_PATTERN.sub(redact_email, sanitised)

        # 4. Redact phones
        def redact_phone(match):
            nonlocal redaction_counts
            # Avoid redacting simple 4-digit years like 2026
            val = match.group(0).strip()
            if len(re.sub(r"\D", "", val)) < 7:
                return val
            redaction_counts["phones"] += 1
            idx = redaction_counts["phones"]
            token = f"[PHONE_REDACTED_{idx}]"
            placeholder_map[token] = val
            return token

        sanitised = PHONE_PATTERN.sub(redact_phone, sanitised)

        # 5. Redact known confidential launch secret terms
        for term in CONFIDENTIAL_TERMS:
            if term.lower() in sanitised.lower():
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                matches = pattern.findall(sanitised)
                for m in matches:
                    redaction_counts["secrets"] += 1
                    idx = redaction_counts["secrets"]
                    token = f"[CONFIDENTIAL_REDACTED_{idx}]"
                    placeholder_map[token] = m
                    sanitised = pattern.sub(token, sanitised, count=1)

        context.sanitised_text = sanitised
        context.placeholder_map = placeholder_map
        context.redaction_log = redaction_counts
        context.flags = flags

        return context
