from fastapi import APIRouter
from typing import List
from app.api.schemas import UserSchema, UserCreate, UserUpdate, TeamSchema

router = APIRouter(tags=["Users & Teams"])

MOCK_TEAMS: List[TeamSchema] = [
    TeamSchema(id="team-social", name="Team Social"),
    TeamSchema(id="team-web", name="Team Web & Growth"),
    TeamSchema(id="team-pr", name="Team PR & Communications"),
]

MOCK_USERS: List[UserSchema] = [
    UserSchema(id="u-creator-social", email="creator.social@lumo.internal", name="Elena Chen", role="creator", max_tier="internal", team_id="team-social", is_active=True),
    UserSchema(id="u-creator-web", email="creator.web@lumo.internal", name="Devon Miles", role="creator", max_tier="internal", team_id="team-web", is_active=True),
    UserSchema(id="u-creator-agency", email="creator.agency@contractor.external", name="Marcus Vance", role="creator", max_tier="public", team_id=None, is_active=True),
    UserSchema(id="u-reviewer", email="reviewer.sarah@lumo.internal", name="Sarah Jenkins", role="reviewer", max_tier="internal", team_id="team-pr", is_active=True),
    UserSchema(id="u-manager", email="manager.kavita@lumo.internal", name="Kavita Rao", role="brand_manager", max_tier="confidential", team_id="team-pr", is_active=True),
    UserSchema(id="u-admin", email="admin@lumo.internal", name="System Admin", role="admin", max_tier="confidential", team_id=None, is_active=True),
]


@router.get("/teams", response_model=List[TeamSchema])
def list_teams():
    return MOCK_TEAMS


@router.get("/users", response_model=List[UserSchema])
def list_users():
    return MOCK_USERS


@router.post("/users", response_model=UserSchema)
def create_user(req: UserCreate):
    return UserSchema(
        id=f"u-{req.email.split('@')[0]}",
        email=req.email,
        name=req.name,
        role=req.role,
        max_tier=req.max_tier,
        team_id=req.team_id,
        is_active=True,
    )


@router.patch("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: str, req: UserUpdate):
    for u in MOCK_USERS:
        if u.id == user_id:
            return u
    return MOCK_USERS[0]
