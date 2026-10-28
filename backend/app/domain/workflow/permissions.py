"""
Pure domain permission policies, classification tier rules, and allowed_actions logic.
Zero dependencies on external frameworks (FastAPI, SQLAlchemy, HTTP).
"""

from typing import List, Dict, Any, Optional

TIER_RANKS: Dict[str, int] = {
    "public": 1,
    "internal": 2,
    "confidential": 3,
}

ROLES = ("creator", "reviewer", "brand_manager", "admin")


def can_access_tier(user_max_tier: str, entry_classification: str) -> bool:
    """Check if user tier is greater than or equal to resource classification tier."""
    user_rank = TIER_RANKS.get(user_max_tier.lower(), 1)
    entry_rank = TIER_RANKS.get(entry_classification.lower(), 1)
    return user_rank >= entry_rank


def can_manage_kb(role: str) -> bool:
    """Only brand_manager and admin can create/edit/retire knowledge base entries."""
    return role in ("brand_manager", "admin")


def can_view_audit(role: str) -> bool:
    """Reviewers, managers and admins can inspect audit logs."""
    return role in ("reviewer", "brand_manager", "admin")


def can_export_audit(role: str) -> bool:
    """Only managers and admins can export audit logs as CSV."""
    return role in ("brand_manager", "admin")


def can_manage_users(role: str) -> bool:
    """Only admin can create or modify system users."""
    return role == "admin"


def normalize_channel(channel: Optional[str]) -> str:
    """
    Normalizes channel string to standard canonical channels:
    'social', 'email', 'blog', 'web', 'press_release'.
    Handles spaces, dashes, case variation, and common aliases.
    """
    if not channel:
        return "web"
    c = str(channel).strip().lower().replace("-", "_").replace(" ", "_")
    if "press" in c or "release" in c or c == "pr":
        return "press_release"
    if "email" in c or "newsletter" in c:
        return "email"
    if "blog" in c or "article" in c:
        return "blog"
    if "social" in c:
        return "social"
    if "web" in c or "site" in c or "landing" in c:
        return "web"
    return c


def get_risk_tier_for_channel(channel: Optional[str]) -> str:
    """Returns 'high' for press_release, 'medium' for email/blog/web, and 'low' for social/others."""
    c = normalize_channel(channel)
    if c == "press_release":
        return "high"
    elif c in ("email", "blog", "web"):
        return "medium"
    return "low"


def get_required_approvals(risk_tier: str) -> int:
    """High-risk submissions require 2 distinct approvals; low and medium require 1."""
    if risk_tier.lower() == "high":
        return 2
    return 1


def compute_submission_allowed_actions(
    submission_status: str,
    submission_creator_id: str,
    submission_risk_tier: str,
    user_id: str,
    user_role: str,
    assignee_id: Optional[str] = None,
    open_high_severity_count: int = 0,
    valid_approvals_reviewer_ids: Optional[List[str]] = None,
) -> List[str]:
    """
    Computes available actions for a user on a given submission based on workflow state machine,
    role-based access control, high-severity gating, and self-approval restrictions.
    """
    if valid_approvals_reviewer_ids is None:
        valid_approvals_reviewer_ids = []

    actions: List[str] = []
    is_creator = (user_id == submission_creator_id)
    is_reviewer_or_above = user_role in ("reviewer", "brand_manager", "admin")
    is_manager_or_admin = user_role in ("brand_manager", "admin")

    if submission_status in ("Draft", "Changes Requested"):
        if is_creator or is_manager_or_admin:
            actions.append("edit")
            actions.append("run_review")
            if submission_status == "Changes Requested":
                # Can resubmit if no blocking high-severity issues
                if open_high_severity_count == 0:
                    actions.append("submit")
            actions.append("delete")

    elif submission_status == "Checked":
        if is_creator or is_manager_or_admin:
            actions.append("edit")
            actions.append("run_review")
            # Invariant: Cannot submit if high-severity open findings exist
            if open_high_severity_count == 0:
                actions.append("submit")
            actions.append("delete")

    elif submission_status == "Submitted":
        if is_creator or is_manager_or_admin:
            actions.append("edit")  # Editing voids submission and returns to Draft
        if is_reviewer_or_above:
            actions.append("claim")

    elif submission_status == "In Review":
        if is_creator or is_manager_or_admin:
            actions.append("edit")  # Editing voids approvals & returns to Draft

        is_assigned = (assignee_id == user_id) or (assignee_id is None and is_reviewer_or_above) or is_manager_or_admin

        if is_assigned:
            actions.append("request_changes")

            # Check self-approval invariant: creator cannot approve own submission
            can_approve = not is_creator

            # If user already gave a valid approval on this version, cannot approve again
            if user_id in valid_approvals_reviewer_ids:
                can_approve = False

            if can_approve:
                actions.append("approve")

            if assignee_id == user_id:
                actions.append("unclaim")

    elif submission_status == "Approved":
        if is_creator or is_manager_or_admin:
            actions.append("mark_published")
            actions.append("edit")  # Editing returns to Draft and voids approval

    elif submission_status == "Marked Published":
        # Published submissions are locked
        pass

    return actions


def compute_finding_allowed_actions(
    finding_status: str,
    submission_creator_id: str,
    user_id: str,
    user_role: str,
) -> List[str]:
    """
    Computes allowed actions on a finding.
    Only creator or manager/admin can accept/dismiss/escalate an open finding.
    """
    if finding_status != "open":
        return []

    is_creator = (user_id == submission_creator_id)
    is_manager_or_admin = user_role in ("brand_manager", "admin")

    if is_creator or is_manager_or_admin:
        return ["accept", "dismiss", "escalate"]

    return []
