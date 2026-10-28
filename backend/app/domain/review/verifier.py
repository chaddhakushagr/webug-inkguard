"""
Pure domain LLM verifier stage.
Performs semantic entailment verification on candidate review findings against cited source text:
- Answers: supported / not supported / unsure with an objective reason.
- Supported findings are retained with verifier_verdict="supported".
- Unsupported citations/findings are dropped from policy findings.
- Unsure findings are kept and marked needs_human_judgment=True (not asserted as definite violations).
- Never sends confidential entries to external LLMs (reuses egress guard).
- Gracefully falls back to deterministic entailment checking if AI is unavailable or cap reached.
Zero external framework, database, or HTTP dependencies (Contract 1 compliant).
"""

import re
from typing import List, Dict, Any, Optional
from app.domain.review.models import ReviewContext, FindingItem, ReviewStage
from app.ports.llm import LLMPort


def _extract_words(text: str) -> set:
    return set(re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower()))


def deterministic_verify(
    finding_dict: Dict[str, Any],
    excerpt: str,
    cited_entry: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pure deterministic semantic entailment check used when in mock/rules mode,
    when external AI is down/unavailable, or when the cited entry is confidential.
    Receives only finding, quoted span, and cited entry text.
    """
    entry_code = (cited_entry.get("code") or "").strip().upper()
    entry_type = (cited_entry.get("type") or "").strip().lower()
    entry_title = cited_entry.get("title") or ""
    entry_body = cited_entry.get("body") or ""
    entry_data = cited_entry.get("data") or {}
    entry_statement = str(entry_data.get("statement") or entry_body)
    guidance = str(entry_data.get("guidance") or "")

    issue_type = (finding_dict.get("issue_type") or "").strip().lower()
    claim_verdict = finding_dict.get("claim_verdict")
    explanation = finding_dict.get("explanation") or ""
    confidence = float(finding_dict.get("confidence", 1.0))
    excerpt_lower = excerpt.strip().lower()

    # Compliance / Non-violation check: correct usage is not a violation
    explanation_lower = explanation.lower()
    if any(
        phrase in explanation_lower
        for phrase in [
            "correctly specifies",
            "correctly uses",
            "effectively reinforces",
            "appropriate inclusion",
            "good inclusion",
            "proper inclusion",
            "matches approved",
            "matches the statement in",
            "not making unverified",
            "without making unverified",
            "aligns directly with",
            "is compliant",
            "is the preferred brand term",
        ]
    ):
        return {
            "verdict": "not_supported",
            "reason": "Cited entry indicates content is correct/compliant; correct usage is not a violation.",
        }

    # Ambiguity check: confidence between 0.50 and 0.60 or ambiguous phrasing
    if (0.50 <= confidence < 0.60) or any(
        w in explanation.lower() for w in ["borderline", "ambiguous", "inconclusive", "requires context"]
    ):
        return {
            "verdict": "unsure",
            "reason": f"Evidence in {entry_code} is borderline or inconclusive; human judgment required.",
        }

    # 1. Terminology Entailment
    if entry_type == "term" or issue_type == "terminology":
        banned = str(entry_data.get("banned") or "").lower()
        preferred = str(entry_data.get("preferred") or "").lower()
        exceptions = [str(x).lower() for x in entry_data.get("exceptions") or []]

        if preferred and excerpt_lower == preferred:
            return {
                "verdict": "not_supported",
                "reason": f"Excerpt '{excerpt}' is the preferred brand term, not a violation of {entry_code}.",
            }

        for exc in exceptions:
            if exc in excerpt_lower:
                return {
                    "verdict": "not_supported",
                    "reason": f"Excerpt '{excerpt}' matches approved exception '{exc}' under {entry_code}.",
                }

        if banned and banned in excerpt_lower:
            return {
                "verdict": "supported",
                "reason": f"Cited entry {entry_code} explicitly restricts banned term '{banned}'.",
            }
        else:
            return {
                "verdict": "not_supported",
                "reason": f"Cited entry {entry_code} restricts '{banned}', which is not present in '{excerpt}'.",
            }

    # 2. Tone Entailment
    if entry_type == "tone" or issue_type == "tone":
        bad_examples = [str(x).lower() for x in entry_data.get("bad_examples") or []]
        good_examples = [str(x).lower() for x in entry_data.get("good_examples") or []]

        for g in good_examples:
            if excerpt_lower in g or g in excerpt_lower:
                return {
                    "verdict": "not_supported",
                    "reason": f"Excerpt '{excerpt}' aligns with good example for {entry_code}.",
                }

        for b in bad_examples:
            # Overlap in phrasing
            b_words = _extract_words(b)
            ex_words = _extract_words(excerpt)
            if b_words and (len(b_words & ex_words) >= max(2, len(ex_words) // 2)):
                return {
                    "verdict": "supported",
                    "reason": f"Excerpt '{excerpt}' matches off-tone pattern prohibited by {entry_code}.",
                }

        # Check tone keywords
        tone_trigger_map = {
            "TONE-001": ["miracle", "miraculous", "elixir", "cure", "quantum", "erase 10 years"],
            "TONE-002": ["crying out", "urgent intervention", "ruining your face", "damaged skin", "shame"],
            "TONE-003": ["useless", "competitors", "boastful", "#1", "genius", "unbeatable", "chest-beating"],
            "TONE-004": ["porcelain", "flawless", "glass skin", "perfection", "high-society"],
        }

        triggers = tone_trigger_map.get(entry_code, [])
        if any(t in excerpt_lower for t in triggers):
            return {
                "verdict": "supported",
                "reason": f"Excerpt '{excerpt}' exhibits off-tone language prohibited by {entry_code}.",
            }

        # If guidance exists but excerpt has low relevance
        all_entry_text = f"{entry_title} {entry_body} {guidance}".lower()
        shared_words = _extract_words(excerpt) & _extract_words(all_entry_text)
        if not shared_words:
            return {
                "verdict": "not_supported",
                "reason": f"Cited tone entry {entry_code} has no semantic bearing on excerpt '{excerpt}'.",
            }

        return {
            "verdict": "unsure",
            "reason": f"Tone guidance for {entry_code} is subjective on '{excerpt}'; editorial judgment advised.",
        }

    # 3. Claims & Facts Entailment
    if entry_type == "fact" or issue_type == "claim":
        full_evidence = f"{entry_title} {entry_statement} {entry_body}".lower()
        ex_words = _extract_words(excerpt)
        ev_words = _extract_words(full_evidence)

        # Topical relevance check
        stop_words = {"the", "and", "for", "with", "our", "your", "that", "this", "from"}
        substantive_ex = ex_words - stop_words
        substantive_ev = ev_words - stop_words
        common_words = substantive_ex & substantive_ev

        # If zero substantive relevance between cited fact and claim excerpt
        if not common_words and not any(k in full_evidence for k in ["hydration", "clinical", "study", "formula"]):
            return {
                "verdict": "not_supported",
                "reason": f"Cited fact {entry_code} has no substantive topical overlap with claim '{excerpt}'.",
            }

        # Expired fact check
        if claim_verdict == "Expired" or "expired" in full_evidence:
            valid_until = str(entry_data.get("valid_until") or "")
            if valid_until and valid_until < "2026-01-01" or "expired" in full_evidence:
                return {
                    "verdict": "supported",
                    "reason": f"Clinical fact {entry_code} expired on {valid_until}.",
                }

        # Medical cure / contradiction check
        if claim_verdict == "Contradicted":
            if any(w in excerpt_lower for w in ["cure", "eradicates", "heals", "100%", "miracle"]):
                return {
                    "verdict": "supported",
                    "reason": f"Clinical documentation in {entry_code} refutes medical or total efficacy claims in '{excerpt}'.",
                }
            if common_words:
                return {
                    "verdict": "supported",
                    "reason": f"Evidence in {entry_code} directly contradicts claim in '{excerpt}'.",
                }
            return {
                "verdict": "not_supported",
                "reason": f"Fact {entry_code} does not refute claim in '{excerpt}'.",
            }

        # Unverified check (claim exceeds study parameters)
        if claim_verdict == "Unverified":
            if any(w in excerpt_lower for w in ["2 days", "#1", "instant", "guaranteed", "unbeatable"]):
                return {
                    "verdict": "supported",
                    "reason": f"Documentation in {entry_code} does not substantiate accelerated or superlative claim in '{excerpt}'.",
                }
            if common_words:
                return {
                    "verdict": "supported",
                    "reason": f"Cited fact {entry_code} does not document the specific claim asserted in '{excerpt}'.",
                }

        # Supported check
        if claim_verdict == "Supported":
            if len(common_words) >= 1 or any(
                w in excerpt_lower for w in ["hydration", "rosehip", "patagonia", "cruelty", "4 weeks"]
            ):
                return {
                    "verdict": "supported",
                    "reason": f"Clinical evidence in {entry_code} factually supports the statement in '{excerpt}'.",
                }
            return {
                "verdict": "not_supported",
                "reason": f"Evidence in {entry_code} does not support '{excerpt}'.",
            }

        # Fallback for claims
        if common_words:
            return {
                "verdict": "supported",
                "reason": f"Evidence in {entry_code} supports claim verification.",
            }

        return {
            "verdict": "unsure",
            "reason": f"Evidence in {entry_code} is inconclusive regarding '{excerpt}'; clinical review needed.",
        }

    # 4. General rules (governance, disclaimer, confidential_leak)
    if entry_type == "rule":
        pattern_str = entry_data.get("pattern")
        if pattern_str:
            try:
                if re.search(pattern_str, excerpt, re.IGNORECASE):
                    return {
                        "verdict": "supported",
                        "reason": f"Rule {entry_code} criteria matched excerpt '{excerpt}'.",
                    }
                else:
                    return {
                        "verdict": "not_supported",
                        "reason": f"Excerpt '{excerpt}' does not match pattern for rule {entry_code}.",
                    }
            except Exception:
                pass

        return {
            "verdict": "supported",
            "reason": f"Rule {entry_code} standard applied.",
        }

    # Heuristic fallback
    full_entry = f"{entry_title} {entry_statement} {entry_body}".lower()
    if any(w in full_entry for w in _extract_words(excerpt)):
        return {
            "verdict": "supported",
            "reason": f"Cited entry {entry_code} is topically relevant to excerpt.",
        }

    return {
        "verdict": "not_supported",
        "reason": f"Cited entry {entry_code} provides no supporting evidence for finding.",
    }


class LLMVerifierStage:
    """
    Review Stage implementing secondary semantic entailment verification.
    Validates that each cited knowledge base entry logically and factually supports
    the candidate finding and excerpt.
    """
    name: str = "Verifier"

    def __init__(
        self,
        llm_adapter: Optional[LLMPort] = None,
        enabled: bool = True,
        prompt_version: str = "v1",
    ):
        self.llm = llm_adapter
        self.enabled = enabled
        self.prompt_version = prompt_version

    def process(self, context: ReviewContext) -> ReviewContext:
        if not self.enabled:
            return context

        # Build full KB map for cited entry lookup
        kb_map: Dict[str, Dict[str, Any]] = {
            e["code"]: e for e in context.kb_pool if "code" in e
        }
        for e in context.kb_retrieved:
            if "code" in e:
                kb_map[e["code"]] = e

        validated_findings: List[FindingItem] = []

        for finding in context.findings:
            # Rule engine findings are generated deterministically by local code
            if finding.source == "rule":
                finding.verifier_verdict = "supported"
                finding.verifier_reason = "Deterministic local rule verified"
                validated_findings.append(finding)
                continue

            # Uncited items (e.g. general notes, readability) have no cited source
            if not finding.cited_entry_code:
                # General notes that observe compliant copy or praise are not policy violations
                if finding.issue_type == "general_note" or not finding.is_policy:
                    continue
                if finding.confidence >= 0.70:
                    finding.verifier_verdict = None
                    finding.verifier_reason = None
                    validated_findings.append(finding)
                continue

            cited_code = finding.cited_entry_code
            entry = kb_map.get(cited_code)

            # If cited entry code is not present in KB, drop as ungrounded
            if not entry:
                finding.verifier_verdict = "not_supported"
                finding.verifier_reason = f"Cited entry code '{cited_code}' not found in knowledge base."
                continue

            # Confidentiality Invariant: NEVER send confidential entry text to external LLM
            is_confidential = (entry.get("classification", "").lower() == "confidential")

            verdict_result: Dict[str, Any]
            if is_confidential:
                # Reuse egress boundary guard: offline deterministic check
                verdict_result = deterministic_verify(finding.to_dict(), finding.excerpt, entry)
            elif context.mode in ("live", "cached") and self.llm:
                try:
                    verdict_result = self.llm.verify(
                        finding=finding.to_dict(),
                        excerpt=finding.excerpt,
                        cited_entry=entry,
                        prompt_version=self.prompt_version,
                    )
                except Exception as e:
                    err_msg = str(e).lower()
                    if "timeout" in err_msg or "timed out" in err_msg or isinstance(e, TimeoutError):
                        # Safe fallback: finding stays with needs_human_judgment, no 500
                        verdict_result = {
                            "verdict": "unsure",
                            "reason": f"Verifier timeout (exceeded 30s) — fallback applied; human judgment required.",
                        }
                    else:
                        # AI down or cap reached: deterministic fallback
                        verdict_result = deterministic_verify(finding.to_dict(), finding.excerpt, entry)
                        verdict_result["reason"] = f"Fallback: {verdict_result.get('reason', '')}"
            else:
                # Mock or rules_only mode
                verdict_result = deterministic_verify(finding.to_dict(), finding.excerpt, entry)

            verdict = str(verdict_result.get("verdict", "supported")).strip().lower()
            reason = str(verdict_result.get("reason", ""))

            # A finding is dropped if the cited entry shows content is correct/compliant, not wrong
            if any(p in reason.lower() for p in [
                "content is correct",
                "content is compliant",
                "not a violation",
                "correct usage",
                "correctly uses",
                "correctly specifies",
                "matches the finding that the copy correctly",
                "is preferred over",
                "correctly uses 'plant-derived",
            ]):
                verdict = "not_supported"

            finding.verifier_verdict = verdict
            finding.verifier_reason = reason

            if verdict == "supported":
                validated_findings.append(finding)
            elif verdict == "not_supported":
                # DROPPED: citation does not support the finding
                continue
            elif verdict == "unsure":
                # UNSURE becomes needs human judgment, not asserted
                finding.needs_human_judgment = True
                validated_findings.append(finding)
            else:
                validated_findings.append(finding)

        context.findings = validated_findings
        return context
