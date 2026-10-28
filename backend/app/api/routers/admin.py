from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.adapters.db.session import get_db
from app.adapters.db.models import (
    UploadedDocument,
    Comment,
    Approval,
    FindingAction,
    Finding,
    Review,
    SubmissionVersion,
    Submission,
    Notification,
    KBEntry,
    KBEntryVersion,
)
from app.adapters.db.audit import record_audit
from app.api.dependencies import get_current_user, require_role, AuthenticatedUser
from app.seed.loader import run_seed

router = APIRouter(tags=["Admin & System"])


def _execute_demo_reset(db: Session, admin_user: AuthenticatedUser) -> dict:
    """
    Cleans up user submissions, approvals, notifications and re-runs
    seed loader to guarantee pristine demo data.
    """
    try:
        # Clear dynamic submission and workflow records
        db.query(Notification).delete()
        db.query(UploadedDocument).delete()
        db.query(Comment).delete()
        db.query(Approval).delete()
        db.query(FindingAction).delete()
        db.query(Finding).delete()
        db.query(Review).delete()
        db.query(SubmissionVersion).delete()
        db.query(Submission).delete()
        db.commit()

        # Re-populate pristine seed data
        run_seed(db)

        record_audit(
            db=db,
            action="admin_demo_reset",
            entity_type="system",
            entity_id="root",
            actor_id=admin_user.id,
            actor_role=admin_user.role,
            details={"reset_type": "full_demo_reseed"},
        )
        return {
            "status": "ok",
            "message": "Demo data successfully reset to clean state.",
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demo data: {str(exc)}",
        )


@router.get("/admin/reset-demo")
def reset_demo_get(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("admin")),
):
    """
    GET /api/v1/admin/reset-demo
    Re-seeds the database to clean demo state (Restricted to admin role).
    """
    return _execute_demo_reset(db, current_user)


@router.post("/admin/reset-demo")
def reset_demo_post(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("admin")),
):
    """
    POST /api/v1/admin/reset-demo
    Re-seeds the database to clean demo state (Restricted to admin role).
    """
    return _execute_demo_reset(db, current_user)


@router.post("/system/reset-demo")
def reset_demo_system_post(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("admin")),
):
    """
    POST /api/v1/system/reset-demo (G-13)
    One-click demo data reset matching manage.py seed.
    """
    return _execute_demo_reset(db, current_user)
