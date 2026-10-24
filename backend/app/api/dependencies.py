from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.adapters.db.session import get_db
from app.adapters.db.models import User
from app.adapters.security import decode_access_token
from app.domain.workflow.permissions import can_access_tier
from app.config import settings

security_bearer = HTTPBearer(auto_error=False)

# Fallback in-memory users for demo mode before seed or during quick runs
FALLBACK_USERS = {
    "u-creator-social": {
        "id": "u-creator-social",
        "name": "Elena Chen",
        "email": "creator.social@lumo.internal",
        "role": "creator",
        "max_tier": "internal",
        "team": "Team Social",
    },
    "u-creator-agency": {
        "id": "u-creator-agency",
        "name": "Marcus Vance",
        "email": "creator.agency@contractor.external",
        "role": "creator",
        "max_tier": "public",
        "team": "External Agency",
    },
    "u-reviewer": {
        "id": "u-reviewer",
        "name": "Sarah Jenkins",
        "email": "reviewer.sarah@lumo.internal",
        "role": "reviewer",
        "max_tier": "internal",
        "team": "Brand Review",
    },
    "u-manager": {
        "id": "u-manager",
        "name": "Kavita Rao",
        "email": "manager.kavita@lumo.internal",
        "role": "brand_manager",
        "max_tier": "confidential",
        "team": "Brand Strategy",
    },
    "u-admin": {
        "id": "u-admin",
        "name": "System Admin",
        "email": "admin@lumo.internal",
        "role": "admin",
        "max_tier": "confidential",
        "team": "Operations",
    },
}


class AuthenticatedUser:
    """Lightweight representation of the active session user."""
    def __init__(self, id: str, name: str, email: str, role: str, max_tier: str, team: Optional[str] = None):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.max_tier = max_tier
        self.team = team

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "max_tier": self.max_tier,
            "team": self.team,
        }


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """
    Extracts Bearer JWT, validates signature and expiry, and returns AuthenticatedUser.
    Raises 401 on missing, expired, or invalid tokens.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Support mock token prefixes in DEMO_MODE for backwards compatibility
    if settings.DEMO_MODE and token.startswith("mock-jwt-token-"):
        user_key = token.replace("mock-jwt-token-", "")
        # Map user_key
        if user_key in FALLBACK_USERS:
            info = FALLBACK_USERS[user_key]
            return AuthenticatedUser(**info)
        # Search by role
        for u in FALLBACK_USERS.values():
            if u["role"] == user_key:
                return AuthenticatedUser(**u)
        # Fallback to social creator
        return AuthenticatedUser(**FALLBACK_USERS["u-creator-social"])

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        team_name = db_user.team.name if db_user.team else None
        return AuthenticatedUser(
            id=db_user.id,
            name=db_user.name,
            email=db_user.email,
            role=db_user.role,
            max_tier=db_user.max_tier,
            team=team_name,
        )

    # In DEMO_MODE, if user is in fallback users or payload
    if settings.DEMO_MODE and user_id in FALLBACK_USERS:
        return AuthenticatedUser(**FALLBACK_USERS[user_id])

    if payload.get("email") and payload.get("role"):
        return AuthenticatedUser(
            id=user_id,
            name=payload.get("name", "Demo User"),
            email=payload.get("email"),
            role=payload.get("role", "creator"),
            max_tier=payload.get("max_tier", "internal"),
            team=payload.get("team"),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*allowed_roles: str) -> Callable:
    """Dependency factory checking that user role is in allowed_roles."""
    def role_checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action forbidden for role '{current_user.role}'. Required: {list(allowed_roles)}",
            )
        return current_user
    return role_checker


def require_tier(required_tier: str) -> Callable:
    """Dependency factory checking user classification clearance."""
    def tier_checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not can_access_tier(current_user.max_tier, required_tier):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Classification clearance '{current_user.max_tier}' insufficient for '{required_tier}' resource",
            )
        return current_user
    return tier_checker
