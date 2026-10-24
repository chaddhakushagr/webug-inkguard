"""
Pure domain suggestion validator stage.
Ensures minimal-edit replacements:
- Rejects changes altering more than 60% of original span
- Rejects suggestions introducing numbers or percentages absent from original and cited evidence
- Rejects suggestions introducing superlatives or prohibited terms
"""

import re
from typing import Tuple, Optional, Set
from app.domain.review.models import ReviewContext, FindingItem, ReviewStage

PROHIBITED_SUPERLATIVES = {
    "miracle", "miraculous", "guaranteed", "#1", "number one", "unbeatable",
    "best in class", "cure", "flawless", "ultimate", "revolutionary", "greatest"
}

BANNED_TERMS = {
    "serum", "cure", "toxin-free", "chemical-free", "all-natural", "instant fix"
}


def extract_numbers_and_percentages(text: str) -> Set[str]:
    """Finds all digits and percentage tokens."""
    return set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text.lower()))


def calculate_char_difference_ratio(original: str, replacement: str) -> float:
    """Computes basic edit difference ratio."""
    o_len = len(original.strip())
    r_len = len(replacement.strip())
    if o_len == 0:
        return 1.0

    # Overlap calculation
    o_set = set(original.lower().split())
    r_set = set(replacement.lower().split())
    intersection = o_set.intersection(r_set)
    union = o_set.union(r_set)
    if not union:
        return 0.0

    jaccard_distance = 1.0 - (len(intersection) / len(union))
    length_ratio = abs(o_len - r_len) / max(o_len, r_len)
    return max(jaccard_distance, length_ratio)


def validate_suggestion(
    original_excerpt: str,
    suggestion: str,
    cited_evidence_text: str = "",
) -> Tuple[bool, Optional[str]]:
    """
    Validates replacement suggestion against safety and minimal-edit invariants.
    Returns (is_valid, rejection_reason).
    """
    if not suggestion or not suggestion.strip():
        return False, "Suggestion is empty"

    orig_clean = original_excerpt.strip()
    sugg_clean = suggestion.strip()
    sugg_lower = sugg_clean.lower()

    # 1. Check for banned terms first
    for term in BANNED_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", sugg_lower):
            return False, f"Suggestion introduces banned term '{term}'"

    # 2. Check for prohibited superlatives
    for sup in PROHIBITED_SUPERLATIVES:
        if re.search(rf"\b{re.escape(sup)}\b", sugg_lower):
            return False, f"Suggestion introduces prohibited superlative '{sup}'"

    # 3. Check for new ungrounded numbers or percentages
    orig_nums = extract_numbers_and_percentages(orig_clean)
    evidence_nums = extract_numbers_and_percentages(cited_evidence_text)
    allowed_nums = orig_nums.union(evidence_nums)

    sugg_nums = extract_numbers_and_percentages(sugg_clean)
    new_nums = sugg_nums - allowed_nums
    if new_nums:
        return False, f"Suggestion introduces ungrounded numbers or percentages: {list(new_nums)}"

    # 4. Check change cap (max 60% difference)
    diff_ratio = calculate_char_difference_ratio(orig_clean, sugg_clean)
    if diff_ratio > 0.60:
        return False, f"Suggestion alters {diff_ratio*100:.0f}% of text, exceeding the 60% change cap"

    return True, None


class SuggestionValidatorStage:
    name: str = "Suggest"

    def process(self, context: ReviewContext) -> ReviewContext:
        evidence_texts = {
            entry["code"]: entry.get("body", "") + " " + str(entry.get("data", {}))
            for entry in context.kb_retrieved
            if "code" in entry
        }

        for finding in context.findings:
            if finding.suggested_fix:
                # Pre-approved canonical terminology replacements from KB are valid by definition
                if finding.source == "rule" and finding.issue_type == "terminology":
                    continue

                cited_evidence = ""
                if finding.cited_entry_code and finding.cited_entry_code in evidence_texts:
                    cited_evidence = evidence_texts[finding.cited_entry_code]

                is_valid, reason = validate_suggestion(
                    original_excerpt=finding.excerpt,
                    suggestion=finding.suggested_fix,
                    cited_evidence_text=cited_evidence,
                )

                if not is_valid:
                    # Reject unsafe suggestion
                    finding.suggested_fix = None
                    finding.needs_human_judgment = True

        return context
