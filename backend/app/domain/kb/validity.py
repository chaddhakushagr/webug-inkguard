"""
Pure domain logic for knowledge base fact validity and expiry checks.
Zero framework or external dependencies.
"""

from datetime import datetime, date, timezone
from typing import Dict, Any, Optional


def parse_date(date_val: Any) -> Optional[date]:
    if not date_val:
        return None
    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        try:
            return datetime.fromisoformat(date_val.replace("Z", "+00:00")).date()
        except Exception:
            try:
                return datetime.strptime(date_val[:10], "%Y-%m-%d").date()
            except Exception:
                return None
    return None


def check_fact_validity(data: Dict[str, Any], reference_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Evaluates validity of a fact based on valid_from and valid_until timestamps.
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc).date()

    valid_from = parse_date(data.get("valid_from"))
    valid_until = parse_date(data.get("valid_until"))

    if valid_from and reference_date < valid_from:
        return {
            "status": "not_yet_effective",
            "is_valid": False,
            "is_expired": False,
            "is_expiring_soon": False,
            "days_left": None,
            "verdict": "Unverified",
            "reason": f"Fact is not effective until {valid_from.isoformat()}",
        }

    if valid_until:
        days_left = (valid_until - reference_date).days
        if days_left < 0:
            return {
                "status": "expired",
                "is_valid": False,
                "is_expired": True,
                "is_expiring_soon": False,
                "days_left": days_left,
                "verdict": "Expired",
                "reason": f"Fact expired on {valid_until.isoformat()} ({abs(days_left)} days ago)",
            }
        elif days_left <= 30:
            return {
                "status": "expiring_soon",
                "is_valid": True,
                "is_expired": False,
                "is_expiring_soon": True,
                "days_left": days_left,
                "verdict": "Valid",
                "reason": f"Fact expires soon on {valid_until.isoformat()} ({days_left} days remaining)",
            }
        else:
            return {
                "status": "valid",
                "is_valid": True,
                "is_expired": False,
                "is_expiring_soon": False,
                "days_left": days_left,
                "verdict": "Valid",
                "reason": f"Valid until {valid_until.isoformat()}",
            }

    return {
        "status": "valid",
        "is_valid": True,
        "is_expired": False,
        "is_expiring_soon": False,
        "days_left": None,
        "verdict": "Valid",
        "reason": "Perpetually valid fact (no expiry date specified)",
    }
