import pytest
from app.domain.workflow.permissions import (
    can_access_tier,
    can_manage_kb,
    can_view_audit,
    can_export_audit,
    can_manage_users,
    get_required_approvals,
    compute_submission_allowed_actions,
    compute_finding_allowed_actions,
)


def test_can_access_tier():
    # Public user can only access public
    assert can_access_tier("public", "public") is True
    assert can_access_tier("public", "internal") is False
    assert can_access_tier("public", "confidential") is False

    # Internal user can access public and internal
    assert can_access_tier("internal", "public") is True
    assert can_access_tier("internal", "internal") is True
    assert can_access_tier("internal", "confidential") is False

    # Confidential user can access all
    assert can_access_tier("confidential", "public") is True
    assert can_access_tier("confidential", "internal") is True
    assert can_access_tier("confidential", "confidential") is True


def test_role_capabilities():
    assert can_manage_kb("admin") is True
    assert can_manage_kb("brand_manager") is True
    assert can_manage_kb("creator") is False
    assert can_manage_kb("reviewer") is False

    assert can_view_audit("reviewer") is True
    assert can_view_audit("creator") is False

    assert can_export_audit("brand_manager") is True
    assert can_export_audit("reviewer") is False

    assert can_manage_users("admin") is True
    assert can_manage_users("brand_manager") is False


def test_required_approvals():
    assert get_required_approvals("low") == 1
    assert get_required_approvals("medium") == 1
    assert get_required_approvals("high") == 2


def test_creator_cannot_approve_own_submission():
    # In Review: reviewer can approve, but creator cannot
    actions_creator = compute_submission_allowed_actions(
        submission_status="In Review",
        submission_creator_id="user-1",
        submission_risk_tier="low",
        user_id="user-1",  # Creator is also the user looking
        user_role="reviewer",  # Even if user has reviewer role!
        assignee_id="user-1",
    )
    assert "approve" not in actions_creator

    # Different user can approve
    actions_reviewer = compute_submission_allowed_actions(
        submission_status="In Review",
        submission_creator_id="user-1",
        submission_risk_tier="low",
        user_id="user-2",
        user_role="reviewer",
        assignee_id="user-2",
    )
    assert "approve" in actions_reviewer


def test_high_severity_blocks_submission():
    # When status is Checked and open_high_severity_count > 0, submit is blocked
    blocked_actions = compute_submission_allowed_actions(
        submission_status="Checked",
        submission_creator_id="user-1",
        submission_risk_tier="medium",
        user_id="user-1",
        user_role="creator",
        open_high_severity_count=1,
    )
    assert "submit" not in blocked_actions

    # When 0 high severity open, submit is allowed
    allowed_actions = compute_submission_allowed_actions(
        submission_status="Checked",
        submission_creator_id="user-1",
        submission_risk_tier="medium",
        user_id="user-1",
        user_role="creator",
        open_high_severity_count=0,
    )
    assert "submit" in allowed_actions


def test_finding_allowed_actions():
    # Creator on open finding
    assert compute_finding_allowed_actions("open", "user-1", "user-1", "creator") == ["accept", "dismiss", "escalate"]
    # Non-creator without admin
    assert compute_finding_allowed_actions("open", "user-1", "user-2", "creator") == []
    # Brand manager can always act
    assert compute_finding_allowed_actions("open", "user-1", "user-3", "brand_manager") == ["accept", "dismiss", "escalate"]
    # Closed finding
    assert compute_finding_allowed_actions("accepted", "user-1", "user-1", "creator") == []
