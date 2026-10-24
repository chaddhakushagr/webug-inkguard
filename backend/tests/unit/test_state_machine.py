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
