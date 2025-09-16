"""
Auth Dependency
"""

from fastapi import Request, HTTPException
from app.utils.auth import get_current_user_id


def resolve_user_id(request: Request) -> str:
    try:
        return get_current_user_id(request)
    except ValueError as e:
        # Bad/missing auth, surface as 400 (or 401/403 if you prefer)
        raise HTTPException(status_code=400, detail=str(e))
