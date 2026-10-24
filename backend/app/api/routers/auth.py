from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.api.schemas import (
    LoginRequest,
    TokenResponse,
    HealthResponse,
    SystemStatusResponse,
    DemoUser,
)
from app.adapters.db.session import get_db
from app.adapters.db.models import User
from app.adapters.security import create_access_token, verify_password, hash_password
from app.api.dependencies import get_current_user, AuthenticatedUser
from app.config import settings

router = APIRouter(tags=["Auth & System"])

DEMO_USERS: List[DemoUser] = [
    DemoUser(
        id="u-creator-social",
        name="Elena Chen",
        email="creator.social@lumo.internal",
        role="creator",
        max_tier="internal",
        team="Team Social",
        description="Social Media Copywriter (Drafts & submits short-form campaigns)",
    ),
    DemoUser(
        id="u-creator-agency",
        name="Marcus Vance",
        email="creator.agency@contractor.external",
        role="creator",
        max_tier="public",
        team="External Agency",
        description="External Contractor (Restricted strictly to public knowledge base items)",
    ),
    DemoUser(
        id="u-reviewer",
        name="Sarah Jenkins",
        email="reviewer.sarah@lumo.internal",
        role="reviewer",
        max_tier="internal",
        team="Brand Review",
        description="Senior Brand Reviewer (Reviews queue, requests changes, issues approvals)",
    ),
    DemoUser(
        id="u-manager",
        name="Kavita Rao",
        email="manager.kavita@lumo.internal",
        role="brand_manager",
        max_tier="confidential",
        team="Brand Strategy",
        description="Brand Director (Manages guidelines, inspects insights, resolves escalations)",
    ),
    DemoUser(
        id="u-admin",
        name="System Admin",
        email="admin@lumo.internal",
        role="admin",
        max_tier="confidential",
        team="Operations",
        description="Administrator (Manages system settings, AI killswitches, egress policy)",
    ),
]


@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="ok",
        version="0.2.0",
        db="healthy",
        ai_mode=settings.LLM_MODE,
    )


@router.get("/system/status", response_model=SystemStatusResponse)
def get_system_status():
    return SystemStatusResponse(
        version="0.2.0",
        commit="05fbbb2",
        ai_mode=settings.LLM_MODE,
        ai_provider="Google AI Studio" if settings.LLM_API_KEY else "Offline Mock Engine",
        health="healthy",
        daily_quota_limit=settings.LLM_DAILY_CAP,
        daily_calls_made=0,
        uptime_seconds=3600,
        db_connected=True,
    )


@router.get("/auth/demo-users", response_model=List[DemoUser])
def get_demo_users():
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo users are only available when DEMO_MODE is active",
        )
    return DEMO_USERS


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()

    # 1. Check in real database
    db_user = db.query(User).filter(User.email.ilike(email)).first()
    if db_user:
        # Verify password if hashed, or in demo mode accept DEMO_PASSWORD
        valid = False
        if req.password == settings.DEMO_PASSWORD and settings.DEMO_MODE:
            valid = True
        elif db_user.password_hash and verify_password(req.password, db_user.password_hash):
            valid = True

        if not valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        team_name = db_user.team.name if db_user.team else None
        token = create_access_token({
            "sub": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "role": db_user.role,
            "max_tier": db_user.max_tier,
            "team": team_name,
        })
        return TokenResponse(
            access_token=token,
            user={
                "id": db_user.id,
                "name": db_user.name,
                "email": db_user.email,
                "role": db_user.role,
                "max_tier": db_user.max_tier,
                "team": team_name,
            },
        )

    # 2. In DEMO_MODE, match demo personas
    if settings.DEMO_MODE:
        for demo in DEMO_USERS:
            if demo.email.lower() == email:
                if req.password and req.password != settings.DEMO_PASSWORD:
                    # Allow blank or DEMO_PASSWORD
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid password for demo user",
                    )
                token = create_access_token({
                    "sub": demo.id,
                    "email": demo.email,
                    "name": demo.name,
                    "role": demo.role,
                    "max_tier": demo.max_tier,
                    "team": demo.team,
                })
                return TokenResponse(
                    access_token=token,
                    user={
                        "id": demo.id,
                        "name": demo.name,
                        "email": demo.email,
                        "role": demo.role,
                        "max_tier": demo.max_tier,
                        "team": demo.team,
                    },
                )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )


@router.get("/auth/me")
def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "max_tier": current_user.max_tier,
        "team": current_user.team,
        "is_active": True,
    }
