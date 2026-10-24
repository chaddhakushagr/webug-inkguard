"""
Pure domain accessibility and readability checks.
Evaluates reading grade level, long sentences, ALL-CAPS runs, "click here" links,
empty markdown image alt text, and heading level skips.
"""

import re
from typing import List, Tuple
from app.domain.review.models import ReviewContext, FindingItem, ReviewStage


def count_syllables(word: str) -> int:
    word = word.lower().strip(".,!?:;\"'()[]{}")
    if not word:
        return 1
    # Simple syllable counting heuristic
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    if word.endswith("e") and not word.endswith("le") and count > 1:
        count -= 1
    return max(1, count)


class A11yChecksStage:
    name: str = "A11yChecks"

    def process(self, context: ReviewContext) -> ReviewContext:
        text = context.text
        findings: List[FindingItem] = list(context.findings)
        seq = len(findings) + 1

        # 1. Reading Grade Level
        words = re.findall(r"\b\w+\b", text)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        if len(words) >= 15 and len(sentences) >= 1:
            syllables = sum(count_syllables(w) for w in words)
            words_per_sentence = len(words) / max(1, len(sentences))
            syllables_per_word = syllables / max(1, len(words))
            grade = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59

            if grade > 14.0:
                findings.append(
                    FindingItem(
                        id=f"find-a11y-{seq:03d}",
                        source="rule",
                        issue_type="readability",
                        severity="medium",
                        confidence=1.0,
                        span_start=0,
                        span_end=min(len(text), 30),
                        excerpt=text[:30],
                        explanation=f"Reading grade level is {grade:.1f} (target is 10-12 for consumer accessibility); simplify complex phrasing.",
                        is_policy=True,
                    )
                )
                seq += 1

        # 2. Very Long Sentences (> 35 words)
        for sentence_match in re.finditer(r"([^.!?\n]+[.!?]?)", text):
            s_text = sentence_match.group(0).strip()
            s_words = re.findall(r"\b\w+\b", s_text)
            if len(s_words) > 35:
                span_start, span_end = sentence_match.span()
                findings.append(
                    FindingItem(
                        id=f"find-a11y-{seq:03d}",
                        source="rule",
                        issue_type="readability",
                        severity="medium",
                        confidence=1.0,
                        span_start=span_start,
                        span_end=span_end,
                        excerpt=s_text[:60] + ("..." if len(s_text) > 60 else ""),
                        explanation=f"Sentence is excessively long ({len(s_words)} words); consider splitting for better readability.",
                        is_policy=True,
                    )
                )
                seq += 1

        # 3. ALL-CAPS runs (3 or more consecutive capitalized words > 2 chars)
        caps_pattern = re.compile(r"\b[A-Z]{3,}(?:\s+[A-Z]{3,}){2,}\b")
        for match in caps_pattern.finditer(text):
            span_start, span_end = match.span()
            excerpt = match.group(0)
            findings.append(
                FindingItem(
                    id=f"find-a11y-{seq:03d}",
                    source="rule",
                    issue_type="accessibility",
                    severity="low",
                    confidence=1.0,
                    span_start=span_start,
                    span_end=span_end,
                    excerpt=excerpt,
                    explanation="Avoid extended runs of ALL-CAPS text; screen readers may spell out letters, and readability is diminished.",
                    suggested_fix=excerpt.capitalize(),
                    is_policy=True,
                )
            )
            seq += 1

        # 4. "Click here" link text
        click_pattern = re.compile(r"(?i)(?:\[\s*click\s+here\s*\]|\bclick\s+here\s+to\b|\bclick\s+here\b)", re.IGNORECASE)
        for match in click_pattern.finditer(text):
            span_start, span_end = match.span()
            excerpt = match.group(0)
            findings.append(
                FindingItem(
                    id=f"find-a11y-{seq:03d}",
                    source="rule",
                    issue_type="accessibility",
                    severity="medium",
                    confidence=1.0,
                    span_start=span_start,
                    span_end=span_end,
                    excerpt=excerpt,
                    explanation="Vague link text 'click here' hinders screen reader navigation; use descriptive anchor text explaining the destination.",
                    is_policy=True,
                )
            )
            seq += 1

        # 5. Markdown images without alt text (![]())
        empty_img_pattern = re.compile(r"!\[\s*\]\(([^)]+)\)")
        for match in empty_img_pattern.finditer(text):
            span_start, span_end = match.span()
            findings.append(
                FindingItem(
                    id=f"find-a11y-{seq:03d}",
                    source="rule",
                    issue_type="accessibility",
                    severity="medium",
                    confidence=1.0,
                    span_start=span_start,
                    span_end=span_end,
                    excerpt=match.group(0),
                    explanation="Image lacks alternative text; add descriptive text in square brackets for visually impaired users.",
                    is_policy=True,
                )
            )
            seq += 1

        # 6. Heading skips (e.g., # to ###)
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        headings: List[Tuple[int, int, int, str]] = []
        for match in heading_pattern.finditer(text):
            level = len(match.group(1))
            start, end = match.span()
            headings.append((level, start, end, match.group(0)))

        for i in range(1, len(headings)):
            prev_level, _, _, _ = headings[i - 1]
            curr_level, start, end, raw = headings[i]
            if curr_level > prev_level + 1:
                findings.append(
                    FindingItem(
                        id=f"find-a11y-{seq:03d}",
                        source="rule",
                        issue_type="accessibility",
                        severity="low",
                        confidence=1.0,
                        span_start=start,
                        span_end=end,
                        excerpt=raw,
                        explanation=f"Heading level skipped from #{prev_level} to #{curr_level}; preserve sequential heading hierarchy.",
                        is_policy=True,
                    )
                )
                seq += 1

        context.findings = findings
        return context
