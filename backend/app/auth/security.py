import json
import logging
import time
from collections import defaultdict
from typing import Optional, List, Dict
from fastapi import HTTPException, Header, Depends, status, Request
from pydantic import BaseModel

from ..config import settings

logger = logging.getLogger(__name__)

class User(BaseModel):
    id: str
    role: str  # "ap_analyst" | "reviewer"
    token: str

class TokenRateLimiter:
    """In-memory rate limiter tracking upload / request timestamps per token."""
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, token_or_id: str):
        now = time.time()
        timestamps = self.requests[token_or_id]
        cutoff = now - self.window_seconds
        # Evict older timestamps
        self.requests[token_or_id] = [ts for ts in timestamps if ts > cutoff]
        if len(self.requests[token_or_id]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: maximum {self.max_requests} requests per {self.window_seconds} seconds allowed."
            )
        self.requests[token_or_id].append(now)

rate_limiter = TokenRateLimiter(max_requests=60, window_seconds=60)

def load_users() -> Dict[str, User]:
    """Loads authorized users mapped by token."""
    users_by_token: Dict[str, User] = {}
    
    if settings.USERS_JSON and settings.USERS_JSON.strip():
        try:
            raw_list = json.loads(settings.USERS_JSON)
            for item in raw_list:
                if "token" in item and "id" in item:
                    u = User(
                        id=str(item["id"]).strip(),
                        role=str(item.get("role", "ap_analyst")).strip().lower(),
                        token=str(item["token"]).strip()
                    )
                    users_by_token[u.token] = u
        except Exception as e:
            logger.error(f"Error parsing USERS_JSON configuration: {e}")

    # Preserved dev fallback only when in development
    if settings.ENVIRONMENT.lower() == "development":
        if "dev-analyst-token" not in users_by_token:
            users_by_token["dev-analyst-token"] = User(id="priya", role="ap_analyst", token="dev-analyst-token")
        if "dev-reviewer-token" not in users_by_token:
            users_by_token["dev-reviewer-token"] = User(id="garv", role="reviewer", token="dev-reviewer-token")
        if "vendorshield-dev-review-token-2026" not in users_by_token:
            users_by_token["vendorshield-dev-review-token-2026"] = User(
                id="authorized_ap_reviewer",
                role="compliance_officer",
                token="vendorshield-dev-review-token-2026"
            )
        if settings.DEV_REVIEWER_TOKEN and settings.DEV_REVIEWER_TOKEN not in users_by_token:
            users_by_token[settings.DEV_REVIEWER_TOKEN] = User(
                id="authorized_ap_reviewer",
                role="reviewer",
                token=settings.DEV_REVIEWER_TOKEN
            )
            
    return users_by_token

def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_reviewer_token: Optional[str] = Header(None)
) -> User:
    """
    Extracts and validates server-derived user identity from Bearer token.
    Applies per-token upload rate limiting.
    """
    if settings.AUTH_DISABLED and settings.ENVIRONMENT.lower() == "development":
        logger.warning("AUTH_DISABLED is active in development mode. Bypassing authentication.")
        return User(id="dev_user", role="reviewer", token="dev_token")

    token = None
    if authorization and authorization.strip().startswith("Bearer "):
        token = authorization.strip().split("Bearer ", 1)[1].strip()
    elif x_reviewer_token:
        token = x_reviewer_token.strip()

    if not token:
        # Dev unauthenticated fallback if explicitly permitted by config
        if settings.REVIEWER_DEV_MODE and settings.ENVIRONMENT.lower() == "development":
            return User(id="dev_unauthenticated_analyst", role="ap_analyst", token="unauthenticated")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing Authorization Bearer token."
        )

    users = load_users()
    user = users.get(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid Bearer authorization token."
        )

    # Rate limit check per authenticated token
    rate_limiter.check_rate_limit(user.token)
    return user

def require_reviewer_role(user: User = Depends(get_current_user)) -> User:
    """Enforces that the authenticated user possesses the 'reviewer' role."""
    if user.role != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Reviewer role required for this action. Authenticated as '{user.role}'."
        )
    return user
