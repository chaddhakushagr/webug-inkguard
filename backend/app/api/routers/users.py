from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.schemas import UserSchema, UserCreate, UserUpdate, TeamSchema
from app.adapters.db.session import get_db
from app.adapters.db.models import User, Team
from app.adapters.security import hash_password
from app.api.dependencies import get_current_user, require_role, AuthenticatedUser
from app.domain.workflow.permissions import ROLES, TIER_RANKS

router = APIRouter(tags=["Users & Teams"])

DEFAULT_TEAMS = [
    {"id": "team-social", "name": "Team Social"},
    {"id": "team-web", "name": "Team Web & Growth"},
    {"id": "team-pr", "name": "Team PR & Communications"},
    {"id": "team-brand", "name": "Brand Strategy"},
    {"id": "team-ops", "name": "Operations"},
]

DEFAULT_USERS = [
    {"id": "u-creator-social", "email": "creator.social@lumo.internal", "name": "Elena Chen", "role": "creator", "max_tier": "internal", "team_id": "team-social", "is_active": True},
    {"id": "u-creator-web", "email": "creator.web@lumo.internal", "name": "Devon Miles", "role": "creator", "max_tier": "internal", "team_id": "team-web", "is_active": True},
    {"id": "u-creator-agency", "email": "creator.agency@contractor.external", "name": "Marcus Vance", "role": "creator", "max_tier": "public", "team_id": None, "is_active": True},
    {"id": "u-reviewer", "email": "reviewer.sarah@lumo.internal", "name": "Sarah Jenkins", "role": "reviewer", "max_tier": "internal", "team_id": "team-pr", "is_active": True},
    {"id": "u-manager", "email": "manager.kavita@lumo.internal", "name": "Kavita Rao", "role": "brand_manager", "max_tier": "confidential", "team_id": "team-brand", "is_active": True},
    {"id": "u-admin", "email": "admin@lumo.internal", "name": "System Admin", "role": "admin", "max_tier": "confidential", "team_id": "team-ops", "is_active": True},
]


@router.get("/teams", response_model=List[TeamSchema])
def list_teams(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    teams = db.query(Team).all()
    if not teams:
        return [TeamSchema(**t) for t in DEFAULT_TEAMS]
    return [TeamSchema(id=t.id, name=t.name) for t in teams]


@router.post("/teams", response_model=TeamSchema)
def create_team(
    team_in: TeamSchema,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("brand_manager", "admin")),
):
    existing = db.query(Team).filter(Team.name == team_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Team '{team_in.name}' already exists",
        )
    team = Team(name=team_in.name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return TeamSchema(id=team.id, name=team.name)


@router.get("/users", response_model=List[UserSchema])
def list_users(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    users = db.query(User).all()
    if not users:
        return [UserSchema(**u) for u in DEFAULT_USERS]
    return [
        UserSchema(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            max_tier=u.max_tier,
            team_id=u.team_id,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Check fallback
        for u in DEFAULT_USERS:
            if u["id"] == user_id:
                return UserSchema(**u)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSchema(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        max_tier=user.max_tier,
        team_id=user.team_id,
        is_active=user.is_active,
    )


@router.post("/users", response_model=UserSchema)
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("admin")),
):
    if req.role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{req.role}'. Valid roles: {list(ROLES)}",
        )
    if req.max_tier not in TIER_RANKS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid max_tier '{req.max_tier}'. Valid tiers: {list(TIER_RANKS.keys())}",
        )

    existing = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{req.email}' already exists",
        )

    # Hash the default demo password or provided password
    pw = req.password if hasattr(req, "password") and req.password else "LumoDemo2026!"
    hashed_pw = hash_password(pw)

    user = User(
        email=req.email.strip().lower(),
        name=req.name.strip(),
        password_hash=hashed_pw,
        role=req.role,
        max_tier=req.max_tier,
        team_id=req.team_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserSchema(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        max_tier=user.max_tier,
        team_id=user.team_id,
        is_active=user.is_active,
    )


@router.patch("/users/{user_id}", response_model=UserSchema)
def update_user(
    user_id: str,
    req: UserUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if req.name is not None:
        user.name = req.name
    if req.role is not None:
        if req.role not in ROLES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid role '{req.role}'")
        user.role = req.role
    if req.max_tier is not None:
        if req.max_tier not in TIER_RANKS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid max_tier '{req.max_tier}'")
        user.max_tier = req.max_tier
    if req.team_id is not None:
        user.team_id = req.team_id
    if req.is_active is not None:
        user.is_active = req.is_active

    db.commit()
    db.refresh(user)

    return UserSchema(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        max_tier=user.max_tier,
        team_id=user.team_id,
        is_active=user.is_active,
    )
