"""
Pure domain accessibility and readability checks.
Evaluates structured documents (DocumentStructure) and text/markdown input:
1. RULE-A11Y-01: Descriptive Hyperlink Guidance ("click here" anchor text).
2. RULE-A11Y-02: Missing Image Alternative Text.
3. RULE-A11Y-03: Heading Order Hierarchy (level skips, e.g. H1 to H3).
4. RULE-A11Y-04: Empty Headings (headings with no text).
5. RULE-A11Y-05: Color Contrast Ratio (< 4.5:1 WCAG AA).
6. RULE-A11Y-06: Reading Grade Level (> 14.0 Flesch-Kincaid).
7. RULE-A11Y-07: Document Title & Tagged PDF checks.
Maps every finding span back to a paragraph/location label.
"""

import re
import hashlib
from typing import List, Tuple, Optional
from app.domain.review.models import ReviewContext, FindingItem


def count_syllables(word: str) -> int:
    word = word.lower().strip(".,!?:;\"'()[]{}")
    if not word:
        return 1
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


def generate_a11y_fingerprint(issue_type: str, excerpt: str, code: Optional[str] = None) -> str:
    raw = f"{issue_type}:{excerpt.strip().lower()}:{code or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def map_text_offset_to_location(text: str, span_start: int) -> str:
    """Fallback location mapper for raw text submissions."""
    if not text or span_start <= 0:
        return "Paragraph 1"
    prefix = text[:span_start]
    paras = prefix.split("\n\n")
    p_num = len(paras)
    return f"Paragraph {p_num}"


class A11yChecksStage:
    name: str = "A11yChecks"

    def process(self, context: ReviewContext) -> ReviewContext:
        text = context.text or ""
        findings: List[FindingItem] = list(context.findings)
        seq = len(findings) + 1
        doc = getattr(context, "document_structure", None)

        # -------------------------------------------------------------
        # Part A: Structured Document Checks (DOCX / PDF)
        # -------------------------------------------------------------
        if doc is not None:
            # 1. Images without Alt Text (RULE-A11Y-02)
            for img in getattr(doc, "images", []):
                if not getattr(img, "has_alt_text", False) or not (getattr(img, "alt_text", "") or "").strip():
                    loc = getattr(img, "location_label", "Document Image")
                    fp = generate_a11y_fingerprint("accessibility", getattr(img, "name", "image"), "RULE-A11Y-02")
                    findings.append(
                        FindingItem(
                            id=f"find-a11y-{seq:03d}",
                            source="rule",
                            issue_type="accessibility",
                            severity="medium",
                            confidence=1.0,
                            span_start=0,
                            span_end=0,
                            excerpt=f"[Image: {getattr(img, 'name', 'Picture')}]",
                            explanation="Image lacks alternative text; add descriptive alt text in image properties for screen readers.",
                            cited_entry_code="RULE-A11Y-02",
                            is_policy=True,
                            location=loc,
                            fingerprint=fp,
                        )
                    )
                    seq += 1

            # 2. Heading Skips & Empty Headings (RULE-A11Y-03, RULE-A11Y-04)
            heading_blocks = [
                b for b in getattr(doc, "blocks", [])
                if getattr(b, "block_type", "") == "heading" and getattr(b, "level", None) is not None
            ]

            # Check empty headings
            for b in heading_blocks:
                b_text = (getattr(b, "text", "") or "").strip()
                if not b_text:
                    loc = getattr(b, "location_label", f"Heading {b.level}")
                    fp = generate_a11y_fingerprint("accessibility", f"empty-h{b.level}", "RULE-A11Y-04")
                    findings.append(
                        FindingItem(
                            id=f"find-a11y-{seq:03d}",
                            source="rule",
                            issue_type="accessibility",
                            severity="medium",
                            confidence=1.0,
                            span_start=getattr(b, "char_start", 0),
                            span_end=getattr(b, "char_end", 0),
                            excerpt=f"[Empty Heading Level {b.level}]",
                            explanation=f"Heading level {b.level} is empty; headings must contain descriptive text for navigation.",
                            cited_entry_code="RULE-A11Y-04",
                            is_policy=True,
                            location=loc,
                            fingerprint=fp,
                        )
                    )
                    seq += 1

            # Check heading level hierarchy skips
            for i in range(1, len(heading_blocks)):
                prev_lvl = heading_blocks[i - 1].level
                curr_lvl = heading_blocks[i].level
                if curr_lvl > prev_lvl + 1:
                    curr_b = heading_blocks[i]
                    loc = getattr(curr_b, "location_label", f"Heading {curr_lvl}")
                    excerpt_text = (getattr(curr_b, "text", "") or "").strip() or f"Heading {curr_lvl}"
                    fp = generate_a11y_fingerprint("accessibility", excerpt_text[:40], "RULE-A11Y-03")
                    findings.append(
                        FindingItem(
                            id=f"find-a11y-{seq:03d}",
                            source="rule",
                            issue_type="accessibility",
                            severity="low",
                            confidence=1.0,
                            span_start=getattr(curr_b, "char_start", 0),
                            span_end=getattr(curr_b, "char_end", 0),
                            excerpt=excerpt_text[:50],
                            explanation=f"Heading level skipped from Heading {prev_lvl} to Heading {curr_lvl}; preserve sequential heading hierarchy.",
                            cited_entry_code="RULE-A11Y-03",
                            is_policy=True,
                            location=loc,
                            fingerprint=fp,
                        )
                    )
                    seq += 1

            # 3. "Click here" link text in structured links (RULE-A11Y-01)
            vague_link_re = re.compile(r"(?i)\b(click\s+here|click\s+here\s+to|here)\b")
            for link in getattr(doc, "links", []):
                link_text = (getattr(link, "text", "") or "").strip()
                if vague_link_re.search(link_text):
                    loc = getattr(link, "location_label", "Link")
                    fp = generate_a11y_fingerprint("accessibility", link_text, "RULE-A11Y-01")
                    findings.append(
                        FindingItem(
                            id=f"find-a11y-{seq:03d}",
                            source="rule",
                            issue_type="accessibility",
                            severity="medium",
                            confidence=1.0,
                            span_start=0,
                            span_end=min(len(link_text), 30),
                            excerpt=link_text,
                            explanation="Vague link text 'click here' hinders screen reader navigation; use descriptive anchor text explaining the destination.",
                            cited_entry_code="RULE-A11Y-01",
                            is_policy=True,
                            location=loc,
                            fingerprint=fp,
                        )
                    )
                    seq += 1

            # 4. Low-contrast font runs (RULE-A11Y-05)
            for run_item in getattr(doc, "low_contrast_runs", []):
                run_text = run_item.get("text", "")
                hex_color = run_item.get("color_hex", "#unknown")
                cr = run_item.get("contrast_ratio", 1.0)
                loc = run_item.get("location_label", "Document")
                fp = generate_a11y_fingerprint("accessibility", run_text[:30], "RULE-A11Y-05")
                findings.append(
                    FindingItem(
                        id=f"find-a11y-{seq:03d}",
                        source="rule",
                        issue_type="accessibility",
                        severity="medium",
                        confidence=1.0,
                        span_start=0,
                        span_end=min(len(run_text), 40),
                        excerpt=run_text[:60],
                        explanation=f"Text color ({hex_color}) has a low contrast ratio of {cr}:1 against background (WCAG AA requires >= 4.5:1).",
                        cited_entry_code="RULE-A11Y-05",
                        is_policy=True,
                        location=loc,
                        fingerprint=fp,
                    )
                )
                seq += 1

            # 5. PDF title and tagging checks (RULE-A11Y-07)
            if getattr(doc, "format", "") == "pdf":
                if not getattr(doc, "title", None):
                    fp = generate_a11y_fingerprint("accessibility", "missing-pdf-title", "RULE-A11Y-07")
                    findings.append(
                        FindingItem(
                            id=f"find-a11y-{seq:03d}",
                            source="rule",
                            issue_type="accessibility",
                            severity="low",
                            confidence=1.0,
                            span_start=0,
                            span_end=0,
                            excerpt="[Document Metadata: Title missing]",
                            explanation="PDF document lacks a Title property in metadata, required for screen reader identification.",
                            cited_entry_code="RULE-A11Y-07",
                            is_policy=True,
                            location="Document Properties",
                            fingerprint=fp,
                        )
                    )
                    seq += 1

                if getattr(doc, "is_tagged_pdf", None) is False and not getattr(doc, "is_scanned", False):
                    fp = generate_a11y_fingerprint("accessibility", "untagged-pdf", "RULE-A11Y-07")
                    findings.append(
                        FindingItem(
                            id=f"find-a11y-{seq:03d}",
                            source="rule",
                            issue_type="accessibility",
                            severity="low",
                            confidence=1.0,
                            span_start=0,
                            span_end=0,
                            excerpt="[Document Catalog: Untagged PDF]",
                            explanation="PDF is not tagged; tagged PDF structure enables assistive technologies to determine logical reading order.",
                            cited_entry_code="RULE-A11Y-07",
                            is_policy=True,
                            location="Document Structure",
                            fingerprint=fp,
                        )
                    )
                    seq += 1

            # 6. Visual Findings from Image Intake (Palette check, Logo match, etc.)
            for vf in getattr(doc, "visual_findings", []):
                fp = generate_a11y_fingerprint(
                    vf.get("issue_type", "visual"),
                    vf.get("excerpt", "")[:40],
                    vf.get("cited_entry_code"),
                )
                findings.append(
                    FindingItem(
                        id=f"find-visual-{seq:03d}",
                        source="rule",
                        issue_type=vf.get("issue_type", "visual"),
                        severity=vf.get("severity", "medium"),
                        confidence=vf.get("confidence", 1.0),
                        span_start=vf.get("span_start", 0),
                        span_end=vf.get("span_end", 0),
                        excerpt=vf.get("excerpt", ""),
                        explanation=vf.get("explanation", ""),
                        cited_entry_code=vf.get("cited_entry_code"),
                        is_policy=vf.get("is_policy", True),
                        location=vf.get("location", "Image"),
                        fingerprint=fp,
                    )
                )
                seq += 1

        # -------------------------------------------------------------
        # Part B: Text/Markdown Checks (applicable to all text inputs)
        # -------------------------------------------------------------
        # Skip text readability / markdown checks on system fallback strings
        if text.startswith("[Image submitted."):
            context.findings = findings
            return context

        # 1. Reading Grade Level (RULE-A11Y-06)
        words = re.findall(r"\b\w+\b", text)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        if len(words) >= 15 and len(sentences) >= 1:
            syllables = sum(count_syllables(w) for w in words)
            words_per_sentence = len(words) / max(1, len(sentences))
            syllables_per_word = syllables / max(1, len(words))
            grade = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59

            if grade > 14.0:
                loc = doc.find_location(0, 30) if doc else map_text_offset_to_location(text, 0)
                fp = generate_a11y_fingerprint("readability", text[:30], "RULE-A11Y-06")
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
                        cited_entry_code="RULE-A11Y-06",
                        is_policy=True,
                        location=loc,
                        fingerprint=fp,
                    )
                )
                seq += 1

        # 2. Text "Click here" link text (RULE-A11Y-01) - only if no doc links already flagged
        already_has_click_here = any(f.cited_entry_code == "RULE-A11Y-01" for f in findings)
        if not already_has_click_here:
            click_pattern = re.compile(
                r"(?i)(?:\[\s*click\s+here\s*\]|\bclick\s+here\s+to\b|\bclick\s+here\b)",
                re.IGNORECASE,
            )
            for match in click_pattern.finditer(text):
                span_start, span_end = match.span()
                excerpt = match.group(0)
                loc = doc.find_location(span_start, span_end) if doc else map_text_offset_to_location(text, span_start)
                fp = generate_a11y_fingerprint("accessibility", excerpt, "RULE-A11Y-01")
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
                        cited_entry_code="RULE-A11Y-01",
                        is_policy=True,
                        location=loc,
                        fingerprint=fp,
                    )
                )
                seq += 1

        # 3. Markdown images without alt text (RULE-A11Y-02)
        already_has_alt_finding = any(f.cited_entry_code == "RULE-A11Y-02" for f in findings)
        if not already_has_alt_finding:
            empty_img_pattern = re.compile(r"!\[\s*\]\(([^)]+)\)")
            for match in empty_img_pattern.finditer(text):
                span_start, span_end = match.span()
                excerpt = match.group(0)
                loc = doc.find_location(span_start, span_end) if doc else map_text_offset_to_location(text, span_start)
                fp = generate_a11y_fingerprint("accessibility", excerpt, "RULE-A11Y-02")
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
                        explanation="Image lacks alternative text; add descriptive text in square brackets for visually impaired users.",
                        cited_entry_code="RULE-A11Y-02",
                        is_policy=True,
                        location=loc,
                        fingerprint=fp,
                    )
                )
                seq += 1

        # 4. Markdown Heading Skips & Empty Headings (RULE-A11Y-03, RULE-A11Y-04)
        if doc is None or not any(f.cited_entry_code in ("RULE-A11Y-03", "RULE-A11Y-04") for f in findings):
            heading_pattern = re.compile(r"^(#{1,6})\s*(.*)$", re.MULTILINE)
            md_headings: List[Tuple[int, int, int, str]] = []
            for match in heading_pattern.finditer(text):
                level = len(match.group(1))
                h_text = match.group(2).strip()
                start, end = match.span()
                if not h_text:
                    loc = map_text_offset_to_location(text, start)
                    fp = generate_a11y_fingerprint("accessibility", f"empty-md-h{level}", "RULE-A11Y-04")
                    findings.append(
                        FindingItem(
                            id=f"find-a11y-{seq:03d}",
                            source="rule",
                            issue_type="accessibility",
                            severity="medium",
                            confidence=1.0,
                            span_start=start,
                            span_end=end,
                            excerpt=match.group(0),
                            explanation=f"Empty markdown heading level #{level}; headings must contain text.",
                            cited_entry_code="RULE-A11Y-04",
                            is_policy=True,
                            location=loc,
                            fingerprint=fp,
                        )
                    )
                    seq += 1
                else:
                    md_headings.append((level, start, end, match.group(0)))

            for i in range(1, len(md_headings)):
                prev_lvl, _, _, _ = md_headings[i - 1]
                curr_lvl, start, end, raw = md_headings[i]
                if curr_lvl > prev_lvl + 1:
                    loc = map_text_offset_to_location(text, start)
                    fp = generate_a11y_fingerprint("accessibility", raw, "RULE-A11Y-03")
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
                            explanation=f"Heading level skipped from #{prev_lvl} to #{curr_lvl}; preserve sequential heading hierarchy.",
                            cited_entry_code="RULE-A11Y-03",
                            is_policy=True,
                            location=loc,
                            fingerprint=fp,
                        )
                    )
                    seq += 1

        # 5. Long sentences and ALL-CAPS runs (readability & a11y)
        for sentence_match in re.finditer(r"([^.!?\n]+[.!?]?)", text):
            s_text = sentence_match.group(0).strip()
            s_words = re.findall(r"\b\w+\b", s_text)
            if len(s_words) > 35:
                span_start, span_end = sentence_match.span()
                loc = doc.find_location(span_start, span_end) if doc else map_text_offset_to_location(text, span_start)
                fp = generate_a11y_fingerprint("readability", s_text[:30], None)
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
                        location=loc,
                        fingerprint=fp,
                    )
                )
                seq += 1

        caps_pattern = re.compile(r"\b[A-Z]{3,}(?:\s+[A-Z]{3,}){2,}\b")
        for match in caps_pattern.finditer(text):
            span_start, span_end = match.span()
            excerpt = match.group(0)
            loc = doc.find_location(span_start, span_end) if doc else map_text_offset_to_location(text, span_start)
            fp = generate_a11y_fingerprint("accessibility", excerpt, None)
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
                    location=loc,
                    fingerprint=fp,
                )
            )
            seq += 1

        # -------------------------------------------------------------
        # Part C: Backfill location labels for ALL findings in context
        # -------------------------------------------------------------
        for f in findings:
            if not f.location:
                if doc is not None:
                    f.location = doc.find_location(f.span_start, f.span_end)
                else:
                    f.location = map_text_offset_to_location(text, f.span_start)

        context.findings = findings
        return context
