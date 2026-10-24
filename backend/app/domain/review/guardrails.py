"""
Pure domain guardrails stage.
Validates LLM findings against active retrieved knowledge base entries:
- Drops citations not in retrieved KB
- Drops findings whose excerpt does not match original text
- Evaluates fact expiration in code from valid_until
- Marks findings with confidence < 0.6 as needing human judgment
- Demotes uncited items to non-policy general notes
- Deduplicates against existing rule findings
"""

from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional
from app.domain.review.models import ReviewContext, FindingItem, ReviewStage
from app.domain.kb.validity import check_fact_validity


class GuardrailsStage:
    name: str = "Guardrails"

    def process(self, context: ReviewContext) -> ReviewContext:
        text = context.text
        retrieved_map: Dict[str, Dict[str, Any]] = {
            entry["code"]: entry for entry in context.kb_retrieved if "code" in entry
        }
        validated_findings: List[FindingItem] = []

        # Existing rule finding spans for deduplication
        rule_spans = [
            (f.span_start, f.span_end, f.issue_type)
            for f in context.findings
            if f.source == "rule"
        ]

        for finding in context.findings:
            # Rule findings already have authoritative ground truth from local code
            if finding.source == "rule":
                validated_findings.append(finding)
                continue

            # 1. Excerpt verification: drop findings whose excerpt is not an exact substring
            excerpt = finding.excerpt.strip() if finding.excerpt else ""
            if not excerpt or excerpt.lower() not in text.lower():
                # Drop mismatched excerpt
                continue

            # Re-align exact span offsets within text
            idx = text.lower().find(excerpt.lower())
            if idx != -1:
                finding.span_start = idx
                finding.span_end = idx + len(excerpt)
                finding.excerpt = text[idx : idx + len(excerpt)]

            # 2. Citation verification: drop cited codes that were not retrieved
            if finding.cited_entry_code:
                if finding.cited_entry_code not in retrieved_map:
                    # Dropped fake/unretrieved citation
                    finding.cited_entry_code = None
                    finding.cited_entry_id = None
                    finding.cited_entry_version = None

            # 3. Demote uncited findings to general non-policy notes
            if not finding.cited_entry_code:
                finding.is_policy = False
                finding.issue_type = "general_note"

            # 4. Expired fact decision evaluated strictly in code
            if finding.cited_entry_code and finding.cited_entry_code in retrieved_map:
                entry = retrieved_map[finding.cited_entry_code]
                if entry.get("type") == "fact":
                    data = entry.get("data") or {}
                    validity = check_fact_validity(data)
                    if validity["is_expired"]:
                        finding.claim_verdict = "Expired"
                        finding.explanation = (
                            f"Cited evidence expired on {data.get('valid_until')} ({validity.get('reason')})."
                        )
                    finding.cited_entry_id = entry.get("id")
                    finding.cited_entry_version = entry.get("current_version", 1)

            # 5. Low confidence becomes needs human judgment
            if finding.confidence < 0.6:
                finding.needs_human_judgment = True

            # 6. Deduplicate AI findings that match an existing rule finding on identical span and type
            is_duplicate = False
            for r_start, r_end, r_type in rule_spans:
                if finding.span_start == r_start and finding.span_end == r_end and finding.issue_type == r_type:
                    is_duplicate = True
                    break

            if not is_duplicate:
                validated_findings.append(finding)

        context.findings = validated_findings
        return context
