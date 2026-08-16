from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.crud.user_crud import get_user_by_email
from app.services.auth_service import verify_access_token


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme)
    ],
    db: Annotated[
        Session,
        Depends(get_db)
    ]
):
    """
    Reads JWT token from Authorization header,
    verifies it and returns the logged-in user.
    """

    token = credentials.credentials

    try:
        payload = verify_access_token(
            token
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )

    email = payload.get(
        "sub"
    )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload."
        )

    user = get_user_by_email(
        db,
        email
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )

    return user

"""
File: auth_dependency.py

Purpose:
Checks whether a user is logged in by verifying the JWT token.
If the token is valid, it fetches the user from the PostgreSQL database
and returns the current authenticated user.
"""



"""
===========================================================================
File: auth_dependency.py

Project: ProcureMind AI

Purpose:
--------
Acts as the authentication gatekeeper.
Responsibilities:
-----------------
1. Reads JWT token from the Authorization header.
2. Verifies whether the token is valid.
3. Extracts the logged-in user's email from the token.
4. Finds the user in PostgreSQL.
5. Returns the current authenticated user.
6. Prevents unauthorized users from accessing protected APIs.
===========================================================================
"""