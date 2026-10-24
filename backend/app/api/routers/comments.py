from datetime import datetime, timezone
from fastapi import APIRouter
from typing import List
from app.api.schemas import CommentCreate, CommentResponse

router = APIRouter(tags=["Comments"])
now = datetime.now(timezone.utc)

MOCK_COMMENTS: List[CommentResponse] = [
    CommentResponse(
        id="comm-001",
        submission_id="sub-sample-s1",
        finding_id="find-001",
        parent_id=None,
        author_id="u-reviewer",
        author_name="Sarah Jenkins (Reviewer)",
        body="Please ensure the term 'serum' is replaced throughout the copy before we approve.",
        created_at=now,
    )
]


@router.get("/submissions/{submission_id}/comments", response_model=List[CommentResponse])
def get_comments(submission_id: str):
    return MOCK_COMMENTS


@router.post("/submissions/{submission_id}/comments", response_model=CommentResponse)
def post_comment(submission_id: str, req: CommentCreate):
    new_comm = CommentResponse(
        id=f"comm-{datetime.now().strftime('%M%S')}",
        submission_id=submission_id,
        finding_id=req.finding_id,
        parent_id=req.parent_id,
        author_id="u-creator-social",
        author_name="Elena Chen (Creator)",
        body=req.body,
        created_at=now,
    )
    return new_comm
