"""
Pure Python domain module for Stale Rule & Fact Detection (Round 3 Improvement 2).
Zero web, database, or external library dependencies.

Detection Criteria:
1. Rules not triggered in last 8 weeks (56 days) or never triggered.
2. KB entries past their specified review date (data.review_date < reference_date).
3. Facts expired (valid_until < reference_date) or expiring within 30 days.
4. Rules that cite expired facts (e.g. data.cited_fact or body mentions expired FACT-xxx).
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional, Set
import re


FACT_CODE_REGEX = re.compile(r"\bFACT-[A-Za-z0-9_\-]+\b", re.IGNORECASE)


@dataclass(frozen=True)
class StaleRuleItem:
    entry_id: str
    code: str
    type: str  # "rule", "term", "fact", "tone", "asset"
    title: str
    stale_reasons: List[str]
    severity: str  # "high", "medium", "low"
    last_triggered_at: Optional[str] = None
    valid_until: Optional[str] = None
    review_date: Optional[str] = None
    recommendation: str = ""


def parse_iso_date(val: Any) -> Optional[date]:
    """Safely parses a string or date object into a date."""
    if not val:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            # Handles YYYY-MM-DD
            return datetime.fromisoformat(val.replace("Z", "+00:00")).date()
        except Exception:
            return None
    return None


def detect_stale_rules(
    kb_entries: List[Dict[str, Any]],
    last_triggered_by_code: Dict[str, datetime],
    trigger_counts_last_8_weeks: Dict[str, int],
    reference_time: Optional[datetime] = None,
) -> List[StaleRuleItem]:
    """
    Evaluates KB entries and returns all items matching stale criteria.
    Pure Python logic.
    """
    if reference_time is None:
        reference_time = datetime(2026, 10, 28, 12, 0, 0, tzinfo=timezone.utc)
    
    ref_date = reference_time.date()
    eight_weeks_cutoff = reference_time - timedelta(weeks=8)

    # 1. Identify all expired facts first
    expired_fact_codes: Set[str] = set()
    facts_by_code: Dict[str, Dict[str, Any]] = {}
    
    for entry in kb_entries:
        if entry.get("status") != "active":
            continue
        code = entry.get("code", "")
        etype = entry.get("type", "")
        data = entry.get("data") or {}
        if etype == "fact":
            facts_by_code[code] = entry
            valid_until = parse_iso_date(data.get("valid_until"))
            if valid_until and valid_until < ref_date:
                expired_fact_codes.add(code)

    stale_items: List[StaleRuleItem] = []

    for entry in kb_entries:
        if entry.get("status") != "active":
            continue

        entry_id = str(entry.get("id", ""))
        code = entry.get("code", "")
        etype = entry.get("type", "rule")
        title = entry.get("title", f"Entry {code}")
        data = entry.get("data") or {}
        body = entry.get("body") or ""

        reasons: List[str] = []
        severity = "low"
        recommendations: List[str] = []

        valid_until_date = parse_iso_date(data.get("valid_until"))
        review_date_val = parse_iso_date(data.get("review_date") or data.get("next_review"))

        # Criterion 1: Rules/terms not triggered in last 8 weeks
        if etype in ["rule", "term", "tone"]:
            recent_count = trigger_counts_last_8_weeks.get(code, 0)
            last_ts = last_triggered_by_code.get(code)
            
            if recent_count == 0:
                if last_ts is None:
                    reasons.append("never_triggered")
                    recommendations.append("Rule has never been triggered across review history; evaluate relevance.")
                else:
                    reasons.append("not_triggered_in_8_weeks")
                    recommendations.append("Zero triggers across past 8 weeks; verify whether policy is obsolete.")
                if severity == "low":
                    severity = "medium"

        # Criterion 2: Past review date
        if review_date_val and review_date_val < ref_date:
            days_overdue = (ref_date - review_date_val).days
            reasons.append(f"past_review_date ({days_overdue} days overdue)")
            recommendations.append(f"Scheduled review date ({review_date_val}) has passed; conduct policy audit.")
            if severity in ["low", "medium"]:
                severity = "medium"

        # Criterion 3: Fact expired or expiring soon
        if etype == "fact":
            if valid_until_date:
                if valid_until_date < ref_date:
                    days_expired = (ref_date - valid_until_date).days
                    reasons.append(f"fact_expired ({days_expired} days ago on {valid_until_date})")
                    recommendations.append("Fact validity has expired. Prohibit new marketing claims citing this proof.")
                    severity = "high"
                elif ref_date <= valid_until_date <= ref_date + timedelta(days=30):
                    days_left = (valid_until_date - ref_date).days
                    reasons.append(f"fact_expiring_soon ({days_left} days remaining until {valid_until_date})")
                    recommendations.append("Fact expires within 30 days. Commission updated clinical/lab data or schedule sunset.")
                    if severity != "high":
                        severity = "medium"

        # Criterion 4: Rule that cites expired facts
        cited_facts_found: Set[str] = set()
        if data.get("cited_fact"):
            cf = str(data.get("cited_fact")).upper()
            if cf in expired_fact_codes:
                cited_facts_found.add(cf)
        
        # Scan body for cited FACT codes
        for match in FACT_CODE_REGEX.finditer(body):
            cf = match.group(0).upper()
            if cf in expired_fact_codes:
                cited_facts_found.add(cf)

        if cited_facts_found:
            reasons.append(f"cites_expired_facts: {', '.join(sorted(cited_facts_found))}")
            recommendations.append(f"Rule relies on expired evidence ({', '.join(sorted(cited_facts_found))}). Update citations immediately.")
            severity = "high"

        if reasons:
            stale_items.append(
                StaleRuleItem(
                    entry_id=entry_id,
                    code=code,
                    type=etype,
                    title=title,
                    stale_reasons=reasons,
                    severity=severity,
                    last_triggered_at=last_triggered_by_code.get(code).isoformat() if last_triggered_by_code.get(code) else None,
                    valid_until=valid_until_date.isoformat() if valid_until_date else None,
                    review_date=review_date_val.isoformat() if review_date_val else None,
                    recommendation=" ".join(recommendations),
                )
            )

    # Sort high severity first, then by code
    severity_order = {"high": 0, "medium": 1, "low": 2}
    stale_items.sort(key=lambda x: (severity_order.get(x.severity, 3), x.code))
    return stale_items
