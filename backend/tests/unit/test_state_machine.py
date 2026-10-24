import pytest
from app.domain.workflow.state_machine import (
    WorkflowState,
    WorkflowStateMachine,
    InvalidTransitionError,
    PermissionDeniedError,
)


def test_valid_workflow_progression():
    """Verify normal happy path: Draft -> Checked -> Submitted -> In Review -> Approved -> Marked Published."""
    # Draft -> Checked (system)
    WorkflowStateMachine.validate_transition(
        current_state=WorkflowState.DRAFT,
        target_state=WorkflowState.CHECKED,
        actor_role="system",
        is_creator=False,
    )

    # Checked -> Submitted (creator with no open high findings)
    WorkflowStateMachine.validate_transition(
        current_state=WorkflowState.CHECKED,
        target_state=WorkflowState.SUBMITTED,
        actor_role="creator",
        is_creator=True,
        has_open_high_severity_findings=False,
    )

    # Submitted -> In Review (reviewer claims)
    WorkflowStateMachine.validate_transition(
        current_state=WorkflowState.SUBMITTED,
        target_state=WorkflowState.IN_REVIEW,
        actor_role="reviewer",
        is_creator=False,
    )

    # In Review -> Approved (reviewer approves, distinct approver count met)
    WorkflowStateMachine.validate_transition(
        current_state=WorkflowState.IN_REVIEW,
        target_state=WorkflowState.APPROVED,
        actor_role="reviewer",
        is_creator=False,
        approver_count=1,
        required_approvals=1,
    )

    # Approved -> Marked Published (creator or manager publishes)
    WorkflowStateMachine.validate_transition(
        current_state=WorkflowState.APPROVED,
        target_state=WorkflowState.MARKED_PUBLISHED,
        actor_role="creator",
        is_creator=True,
    )


def test_safety_invariant_creator_cannot_approve_own():
    """AGENTS.md Invariant 1: Creators can never approve their own submission."""
    with pytest.raises(PermissionDeniedError, match="Creators can never approve their own"):
        WorkflowStateMachine.validate_transition(
            current_state=WorkflowState.IN_REVIEW,
            target_state=WorkflowState.APPROVED,
            actor_role="reviewer",
            is_creator=True,  # User is creator of this submission
            approver_count=1,
            required_approvals=1,
        )


def test_cannot_submit_with_open_high_severity_findings():
    """Creator cannot submit content if there are unaddressed high severity policy findings."""
    with pytest.raises(InvalidTransitionError, match="open high-severity findings"):
        WorkflowStateMachine.validate_transition(
            current_state=WorkflowState.CHECKED,
            target_state=WorkflowState.SUBMITTED,
            actor_role="creator",
            is_creator=True,
            has_open_high_severity_findings=True,
        )


def test_multi_approver_requirement_for_high_risk():
    """High risk submissions require 2 distinct approvals."""
    # Only 1 approval present when 2 required -> should fail
    with pytest.raises(InvalidTransitionError, match="Requires 2 distinct approvals"):
        WorkflowStateMachine.validate_transition(
            current_state=WorkflowState.IN_REVIEW,
            target_state=WorkflowState.APPROVED,
            actor_role="reviewer",
            is_creator=False,
            approver_count=1,
            required_approvals=2,
        )

    # 2 approvals present -> should pass
    WorkflowStateMachine.validate_transition(
        current_state=WorkflowState.IN_REVIEW,
        target_state=WorkflowState.APPROVED,
        actor_role="reviewer",
        is_creator=False,
        approver_count=2,
        required_approvals=2,
    )


def test_editing_content_resets_approved_to_draft():
    """Editing content on an approved or checked submission resets state to Draft."""
    WorkflowStateMachine.validate_transition(
        current_state=WorkflowState.APPROVED,
        target_state=WorkflowState.DRAFT,
        actor_role="creator",
        is_creator=True,
    )


@pytest.mark.parametrize(
    "role,is_creator,current_state,target_state,should_succeed",
    [
        # Checked -> Submitted
        ("creator", True, WorkflowState.CHECKED, WorkflowState.SUBMITTED, True),
        ("brand_manager", False, WorkflowState.CHECKED, WorkflowState.SUBMITTED, True),
        ("admin", False, WorkflowState.CHECKED, WorkflowState.SUBMITTED, True),
        ("reviewer", False, WorkflowState.CHECKED, WorkflowState.SUBMITTED, False),
        # Submitted -> In Review (claim)
        ("reviewer", False, WorkflowState.SUBMITTED, WorkflowState.IN_REVIEW, True),
        ("brand_manager", False, WorkflowState.SUBMITTED, WorkflowState.IN_REVIEW, True),
        ("admin", False, WorkflowState.SUBMITTED, WorkflowState.IN_REVIEW, True),
        ("creator", True, WorkflowState.SUBMITTED, WorkflowState.IN_REVIEW, False),
        # In Review -> Changes Requested
        ("reviewer", False, WorkflowState.IN_REVIEW, WorkflowState.CHANGES_REQUESTED, True),
        ("brand_manager", False, WorkflowState.IN_REVIEW, WorkflowState.CHANGES_REQUESTED, True),
        ("admin", False, WorkflowState.IN_REVIEW, WorkflowState.CHANGES_REQUESTED, True),
        ("creator", True, WorkflowState.IN_REVIEW, WorkflowState.CHANGES_REQUESTED, False),
        # In Review -> Approved (self-approval prohibited)
        ("reviewer", True, WorkflowState.IN_REVIEW, WorkflowState.APPROVED, False),
        ("reviewer", False, WorkflowState.IN_REVIEW, WorkflowState.APPROVED, True),
        ("brand_manager", False, WorkflowState.IN_REVIEW, WorkflowState.APPROVED, True),
        ("creator", True, WorkflowState.IN_REVIEW, WorkflowState.APPROVED, False),
        # Approved -> Marked Published
        ("creator", True, WorkflowState.APPROVED, WorkflowState.MARKED_PUBLISHED, True),
        ("brand_manager", False, WorkflowState.APPROVED, WorkflowState.MARKED_PUBLISHED, True),
        ("admin", False, WorkflowState.APPROVED, WorkflowState.MARKED_PUBLISHED, True),
        ("reviewer", False, WorkflowState.APPROVED, WorkflowState.MARKED_PUBLISHED, False),
    ],
)
def test_table_driven_role_transitions(role, is_creator, current_state, target_state, should_succeed):
    can = WorkflowStateMachine.can_transition(
        current_state=current_state,
        target_state=target_state,
        actor_role=role,
        is_creator=is_creator,
        has_open_high_severity_findings=False,
        approver_count=1,
        required_approvals=1,
    )
    assert can == should_succeed, f"Expected {role} (creator={is_creator}) transition {current_state} -> {target_state} to be {should_succeed}"

