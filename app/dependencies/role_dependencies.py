from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.database.models import User
from app.dependencies.auth_dependencies import get_current_user


def require_roles(*allowed_roles: str) -> Callable:
    allowed = {role.lower() for role in allowed_roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        role = (current_user.role or "buyer").lower()
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(sorted(allowed))}.",
            )
        return current_user

    return dependency
