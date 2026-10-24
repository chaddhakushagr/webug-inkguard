"""
Pure domain rule engine stage.
Evaluates terminology, disclaimers, regex rules, claim triggers, and confidential term leaks.
Computes stable character offsets and fingerprints for each finding.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from app.domain.review.models import ReviewContext, FindingItem, ReviewStage


def generate_fingerprint(issue_type: str, excerpt: str, code: Optional[str] = None) -> str:
    raw = f"{issue_type}:{excerpt.strip().lower()}:{code or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class RuleChecksStage:
    name: str = "RuleChecks"

    def process(self, context: ReviewContext) -> ReviewContext:
        text = context.text
        findings: List[FindingItem] = list(context.findings)
        finding_id_seq = len(findings) + 1

        for entry in context.kb_pool:
            etype = entry.get("type")
            data = entry.get("data") or {}
            code = entry.get("code")

            # 1. Terminology checks
            if etype == "term":
                banned = data.get("banned")
                if not banned:
                    continue

                preferred = data.get("preferred", "")
                exceptions = data.get("exceptions", [])
                severity = data.get("severity", "medium")
                reason = data.get("reason", f"Use approved term '{preferred}' instead of '{banned}'.")

                # Search case-insensitively with word boundaries
                pattern = re.compile(rf"\b{re.escape(banned)}\b", re.IGNORECASE)
                for match in pattern.finditer(text):
                    span_start, span_end = match.span()
                    excerpt = match.group(0)

                    # Check exceptions (e.g., "hair serum" for "serum")
                    is_exception = False
                    for exc in exceptions:
                        exc_pat = re.compile(rf"\b{re.escape(exc)}\b", re.IGNORECASE)
                        for exc_match in exc_pat.finditer(text):
                            e_start, e_end = exc_match.span()
                            if e_start <= span_start and span_end <= e_end:
                                is_exception = True
                                break
                        if is_exception:
                            break

                    if is_exception:
                        continue

                    fp = generate_fingerprint("terminology", excerpt, code)
                    findings.append(
                        FindingItem(
                            id=f"find-rule-{finding_id_seq:03d}",
                            source="rule",
                            issue_type="terminology",
                            severity=severity,
                            confidence=1.0,
                            span_start=span_start,
                            span_end=span_end,
                            excerpt=excerpt,
                            explanation=reason,
                            suggested_fix=preferred,
                            cited_entry_code=code,
                            cited_entry_version=entry.get("current_version", 1),
                            is_policy=True,
                            fingerprint=fp,
                        )
                    )
                    finding_id_seq += 1

            # 2. Rules checks (claim_trigger, disclaimer, confidential_term, regex)
            elif etype == "rule":
                rule_type = data.get("rule_type", "regex")
                pattern_str = data.get("pattern")
                severity = data.get("severity", "medium")
                msg = data.get("message", entry.get("title", "Rule violation"))

                if rule_type in ("claim_trigger", "regex", "confidential_term"):
                    if pattern_str:
                        try:
                            pattern = re.compile(pattern_str, re.IGNORECASE)
                            for match in pattern.finditer(text):
                                span_start, span_end = match.span()
                                excerpt = match.group(0)
                                itype = "claim" if rule_type == "claim_trigger" else (
                                    "confidential_leak" if rule_type == "confidential_term" else "tone"
                                )
                                fp = generate_fingerprint(itype, excerpt, code)
                                findings.append(
                                    FindingItem(
                                        id=f"find-rule-{finding_id_seq:03d}",
                                        source="rule",
                                        issue_type=itype,
                                        severity=severity,
                                        confidence=1.0,
                                        span_start=span_start,
                                        span_end=span_end,
                                        excerpt=excerpt,
                                        explanation=msg,
                                        suggested_fix=None,
                                        cited_entry_code=code,
                                        cited_entry_version=entry.get("current_version", 1),
                                        is_policy=True,
                                        needs_human_judgment=data.get("is_ambiguous", False),
                                        fingerprint=fp,
                                    )
                                )
                                finding_id_seq += 1
                        except re.error:
                            pass

                elif rule_type == "disclaimer":
                    req_phrase = data.get("required_phrase")
                    channel_match = (data.get("channel") == context.channel) or not data.get("channel")
                    if req_phrase and channel_match:
                        # Check if required phrase exists in text
                        if req_phrase.lower() not in text.lower():
                            fp = generate_fingerprint("missing_disclaimer", req_phrase, code)
                            findings.append(
                                FindingItem(
                                    id=f"find-rule-{finding_id_seq:03d}",
                                    source="rule",
                                    issue_type="missing_disclaimer",
                                    severity=severity,
                                    confidence=1.0,
                                    span_start=0,
                                    span_end=min(len(text), 20),
                                    excerpt=text[:20] if len(text) > 0 else "[Missing disclaimer]",
                                    explanation=msg,
                                    suggested_fix=f"{text.strip()} {req_phrase}",
                                    cited_entry_code=code,
                                    cited_entry_version=entry.get("current_version", 1),
                                    is_policy=True,
                                    fingerprint=fp,
                                )
                            )
                            finding_id_seq += 1

        context.findings = findings
        return context
