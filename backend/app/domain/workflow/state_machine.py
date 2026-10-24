from typing import Set, Optional, List


class WorkflowState:
    DRAFT = "Draft"
    CHECKED = "Checked"
    SUBMITTED = "Submitted"
    IN_REVIEW = "In Review"
    CHANGES_REQUESTED = "Changes Requested"
    APPROVED = "Approved"
    MARKED_PUBLISHED = "Marked Published"

    ALL_STATES = {
        DRAFT,
        CHECKED,
        SUBMITTED,
        IN_REVIEW,
        CHANGES_REQUESTED,
        APPROVED,
        MARKED_PUBLISHED,
    }


class InvalidTransitionError(Exception):
    def __init__(self, from_state: str, to_state: str, reason: str):
        super().__init__(f"Cannot transition from '{from_state}' to '{to_state}': {reason}")
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason


class PermissionDeniedError(Exception):
    pass


class WorkflowStateMachine:
    """Pure domain workflow state machine enforcing brand governance transitions."""

    @staticmethod
    def can_transition(
        current_state: str,
        target_state: str,
        actor_role: str,
        is_creator: bool,
        has_open_high_severity_findings: bool = False,
        approver_count: int = 0,
        required_approvals: int = 1,
    ) -> bool:
        try:
            WorkflowStateMachine.validate_transition(
                current_state=current_state,
                target_state=target_state,
                actor_role=actor_role,
                is_creator=is_creator,
                has_open_high_severity_findings=has_open_high_severity_findings,
                approver_count=approver_count,
                required_approvals=required_approvals,
            )
            return True
        except (InvalidTransitionError, PermissionDeniedError):
            return False

    @staticmethod
    def validate_transition(
        current_state: str,
        target_state: str,
        actor_role: str,
        is_creator: bool,
        has_open_high_severity_findings: bool = False,
        approver_count: int = 0,
        required_approvals: int = 1,
    ) -> None:
        if target_state not in WorkflowState.ALL_STATES:
            raise InvalidTransitionError(current_state, target_state, "Unknown target state")

        # Draft -> Checked (System review finished)
        if current_state == WorkflowState.DRAFT and target_state == WorkflowState.CHECKED:
            return

        # Content edit resets to Draft
        if current_state in {WorkflowState.CHECKED, WorkflowState.APPROVED, WorkflowState.CHANGES_REQUESTED} and target_state == WorkflowState.DRAFT:
            if not is_creator and actor_role not in {"admin", "brand_manager"}:
                raise PermissionDeniedError("Only creator or brand manager can edit draft content")
            return

        # Checked -> Submitted (Creator submits for review)
        if current_state == WorkflowState.CHECKED and target_state == WorkflowState.SUBMITTED:
            if not is_creator and actor_role not in {"admin", "brand_manager"}:
                raise PermissionDeniedError("Only the creator can submit content for review")
            if has_open_high_severity_findings:
                raise InvalidTransitionError(
                    current_state,
                    target_state,
                    "Cannot submit with open high-severity findings; all must be accepted, dismissed, or escalated",
                )
            return

        # Submitted -> In Review (Reviewer claims)
        if current_state == WorkflowState.SUBMITTED and target_state == WorkflowState.IN_REVIEW:
            if actor_role not in {"reviewer", "brand_manager", "admin"}:
                raise PermissionDeniedError("Only reviewers or managers can claim submissions")
            return

        # In Review -> Changes Requested
        if current_state == WorkflowState.IN_REVIEW and target_state == WorkflowState.CHANGES_REQUESTED:
            if actor_role not in {"reviewer", "brand_manager", "admin"}:
                raise PermissionDeniedError("Only reviewers can request changes")
            return

        # In Review -> Approved
        if current_state == WorkflowState.IN_REVIEW and target_state == WorkflowState.APPROVED:
            if actor_role not in {"reviewer", "brand_manager", "admin"}:
                raise PermissionDeniedError("Only reviewers can approve submissions")
            if is_creator:
                raise PermissionDeniedError("Safety invariant: Creators can never approve their own submissions")
            if approver_count < required_approvals:
                raise InvalidTransitionError(
                    current_state,
                    target_state,
                    f"Requires {required_approvals} distinct approvals, currently has {approver_count}",
                )
            return

        # Approved -> Marked Published
        if current_state == WorkflowState.APPROVED and target_state == WorkflowState.MARKED_PUBLISHED:
            if not is_creator and actor_role not in {"brand_manager", "admin"}:
                raise PermissionDeniedError("Only author or brand manager can mark content as published")
            return

        raise InvalidTransitionError(
            current_state,
            target_state,
            f"Invalid transition from '{current_state}' to '{target_state}'",
        )
