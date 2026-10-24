from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.schemas import CommentCreate, CommentResponse
from app.adapters.db.session import get_db
from app.adapters.db.models import Comment, Submission, User
from app.adapters.db.audit import record_audit
from app.api.dependencies import get_current_user, AuthenticatedUser

router = APIRouter(tags=["Comments"])


def comment_to_response(c: Comment) -> CommentResponse:
    author_name = c.author.name if c.author else "Team Member"
    if c.author and c.author.role:
        author_name = f"{c.author.name} ({c.author.role.title()})"
    return CommentResponse(
        id=c.id,
        submission_id=c.submission_id,
        finding_id=c.finding_id,
        parent_id=c.parent_id,
        author_id=c.author_id,
        author_name=author_name,
        body=c.body,
        created_at=c.created_at,
    )


@router.get("/submissions/{submission_id}/comments", response_model=List[CommentResponse])
def get_submission_comments(
    submission_id: str,
    finding_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    query = db.query(Comment).filter(Comment.submission_id == submission_id)
    if finding_id:
        query = query.filter(Comment.finding_id == finding_id)

    comments = query.order_by(Comment.created_at.asc()).all()
    return [comment_to_response(c) for c in comments]


@router.post("/submissions/{submission_id}/comments", response_model=CommentResponse)
def post_submission_comment(
    submission_id: str,
    req: CommentCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    body_clean = req.body.strip()
    if not body_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Comment body cannot be empty",
        )

    if req.parent_id:
        parent = db.query(Comment).filter(Comment.id == req.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent comment '{req.parent_id}' not found",
            )

    now = datetime.now(timezone.utc)
    comment = Comment(
        submission_id=submission_id,
        finding_id=req.finding_id,
        parent_id=req.parent_id,
        author_id=current_user.id,
        body=body_clean,
        created_at=now,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    record_audit(
        db=db,
        action="comment_create",
        entity_type="comment",
        entity_id=comment.id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        details={
            "submission_id": submission_id,
            "finding_id": req.finding_id,
            "parent_id": req.parent_id,
        },
    )

    return comment_to_response(comment)


@router.get("/findings/{finding_id}/comments", response_model=List[CommentResponse])
def get_finding_comments(
    finding_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    comments = db.query(Comment).filter(Comment.finding_id == finding_id).order_by(Comment.created_at.asc()).all()
    return [comment_to_response(c) for c in comments]
