from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.api.schemas import (
    LoginRequest,
    TokenResponse,
    HealthResponse,
    SystemStatusResponse,
    DemoUser,
)
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
        ai_mode=settings.LLM_MODE,
        ai_provider="Google AI Studio" if settings.LLM_API_KEY else "Offline Mock Engine",
        daily_quota_limit=settings.LLM_DAILY_CAP,
        daily_calls_made=14,
        uptime_seconds=3600,
        db_connected=True,
    )


@router.get("/auth/demo-users", response_model=List[DemoUser])
def get_demo_users():
    return DEMO_USERS


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    # Match demo users or check password
    for user in DEMO_USERS:
        if user.email.lower() == req.email.lower():
            return TokenResponse(
                access_token=f"mock-jwt-token-{user.id}",
                user={
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "max_tier": user.max_tier,
                    "team": user.team,
                },
            )
    # Default fallback demo user
    return TokenResponse(
        access_token="mock-jwt-token-creator",
        user={
            "id": "u-creator-social",
            "name": "Elena Chen",
            "email": req.email,
            "role": "creator",
            "max_tier": "internal",
            "team": "Team Social",
        },
    )


@router.get("/auth/me")
def get_me():
    return {
        "id": "u-creator-social",
        "name": "Elena Chen",
        "email": "creator.social@lumo.internal",
        "role": "creator",
        "max_tier": "internal",
        "team": "Team Social",
        "is_active": True,
    }


@router.get("/settings")
def get_settings():
    return {
        "egress_policy": "redact_pii_no_confidential",
        "no_external_ai": False,
        "daily_cap": settings.LLM_DAILY_CAP,
        "daily_calls_used": 14,
        "risk_tier_mapping": {
            "social": "low",
            "email": "medium",
            "blog": "medium",
            "web": "medium",
            "press_release": "high",
        },
        "thresholds": {
            "confidence_cutoff": 0.6,
            "change_cap_percent": 60,
            "max_content_chars": settings.MAX_CONTENT_CHARS,
        },
    }


@router.put("/settings")
def update_settings(payload: Dict[str, Any]):
    return {"status": "updated", "settings": payload}
