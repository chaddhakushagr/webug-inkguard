"""
Deterministic offline mock LLM adapter implementing LLMPort.
Produces structured findings for samples S1-S5 and arbitrary text based on fixtures.
Works 100% offline with zero network connectivity and zero API key.
"""

from typing import List, Dict, Any, Optional
from app.ports.llm import LLMPort


class MockLLMAdapter:
    """Mock LLM adapter providing deterministic fixture outputs for testing and offline demo."""

    def analyze(
        self,
        sanitised_text: str,
        kb_entries: List[Dict[str, Any]],
        channel: str = "social",
        prompt_version: str = "v1",
    ) -> Dict[str, Any]:
        text_lower = sanitised_text.lower()
        claims = []
        tone = []
        notes = []

        retrieved_codes = {entry.get("code") for entry in kb_entries if "code" in entry}

        # 1. Match: completely cure dry skin (Contradicted by FACT-001)
        if "cure dry skin" in text_lower or "completely cure" in text_lower:
            if "FACT-001" in retrieved_codes:
                claims.append({
                    "excerpt": "completely cure dry skin",
                    "claim_text": "Cure dry skin medical claim",
                    "category": "efficacy",
                    "verdict": "Contradicted",
                    "cited_entry_code": "FACT-001",
                    "confidence": 0.92,
                    "explanation": "Clinical Study L-12 supports 'visible skin hydration improvement', but explicitly refutes complete medical cure claims.",
                })

        # 2. Match: flawless radiance in just 2 days (Unverified by FACT-001)
        if "2 days" in text_lower or "flawless radiance" in text_lower:
            if "FACT-001" in retrieved_codes:
                claims.append({
                    "excerpt": "flawless radiance in just 2 days",
                    "claim_text": "2-day rapid radiance claim",
                    "category": "efficacy",
                    "verdict": "Unverified",
                    "cited_entry_code": "FACT-001",
                    "confidence": 0.88,
                    "explanation": "Trial L-12 evaluated outcomes at 4 weeks; 2-day rapid efficacy is unverified by clinical documentation.",
                })

        # 3. Match: guaranteed #1 formula (Unverified supremacy claim)
        if "#1 formula" in text_lower or "guaranteed #1" in text_lower:
            claims.append({
                "excerpt": "guaranteed #1 formula",
                "claim_text": "Market rank #1 guarantee",
                "category": "rank",
                "verdict": "Unverified",
                "cited_entry_code": "FACT-001" if "FACT-001" in retrieved_codes else None,
                "confidence": 0.85,
                "explanation": "No market share study substantiates #1 ranking or 100% satisfaction guarantee.",
            })

        # 4. Tone matches for S2
        if "competitors are completely useless" in text_lower:
            if "TONE-003" in retrieved_codes:
                tone.append({
                    "attribute_code": "TONE-003",
                    "excerpt": "Competitors are completely useless compared to our genius",
                    "assessment": "off_tone",
                    "confidence": 0.94,
                    "explanation": "Brand Voice (TONE-003: Confident not boastful) forbids disparaging competitor formulations.",
                    "cited_entry_code": "TONE-003",
                })

        if "damaged face is crying out" in text_lower or "urgent intervention" in text_lower:
            if "TONE-002" in retrieved_codes:
                tone.append({
                    "attribute_code": "TONE-002",
                    "excerpt": "Your damaged face is crying out for an urgent intervention",
                    "assessment": "off_tone",
                    "confidence": 0.91,
                    "explanation": "Brand Voice (TONE-002: Warm & Encouraging) prohibits anxiety-inducing shame language.",
                    "cited_entry_code": "TONE-002",
                })

        # 5. Generic note for long sentence or readability if present
        if len(sanitised_text.split()) > 40:
            notes.append({
                "excerpt": sanitised_text[:40],
                "note": "Consider breaking copy into scannable bullet points for digital engagement.",
                "kind": "readability",
            })

        return {
            "claims": claims,
            "tone": tone,
            "notes": notes,
        }

    def suggest_fixes(
        self,
        sanitised_text: str,
        findings: List[Dict[str, Any]],
        kb_entries: List[Dict[str, Any]],
        prompt_version: str = "v1",
    ) -> List[Dict[str, Any]]:
        suggestions = []
        for f in findings:
            fid = f.get("id")
            excerpt = f.get("excerpt", "")
            fix = None

            if "cure dry skin" in excerpt.lower():
                fix = "visibly improve dry skin"
            elif "flawless radiance in just 2 days" in excerpt.lower():
                fix = "radiant-looking hydration"
            elif "guaranteed #1 formula" in excerpt.lower():
                fix = "our signature formula"
            elif "competitors are completely useless" in excerpt.lower():
                fix = "our formula is thoughtfully crafted"
            elif "damaged face is crying out" in excerpt.lower():
                fix = "your skin deserves daily gentle care"
            elif "miracle" in excerpt.lower():
                fix = "proven"
            elif "serum" in excerpt.lower():
                fix = "Lumo Glow Concentrate"

            if fix:
                suggestions.append({
                    "finding_id": fid,
                    "original_excerpt": excerpt,
                    "suggested_fix": fix,
                })

        return suggestions
