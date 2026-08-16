"""
===========================================================================
File: auth_routes.py

Project: ProcureMind AI

Purpose:
--------
Handles authentication-related APIs.

Responsibilities:
-----------------
1. Register a new user.
2. Check whether an email is already registered.
3. Hash user passwords securely before saving them.
4. Authenticate existing users.
5. Generate JWT access tokens after successful login.
6. Return the currently logged-in user's profile using JWT verification.

Important:
----------
/auth/signup and /auth/login are public endpoints.

/auth/me is protected and requires a valid JWT token.
===========================================================================
"""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User

from app.schemas.auth_schema import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse
)

from app.crud.user_crud import (
    create_user,
    get_user_by_email
)

from app.services.security_service import (
    hash_password,
    verify_password
)

from app.services.auth_service import (
    create_access_token
)

from app.dependencies.auth_dependencies import (
    get_current_user
)


# -------------------------------------------------------------------------
# Create Authentication Router
#
# Important:
# We DO NOT protect the complete router because
# signup and login must remain public.
# -------------------------------------------------------------------------

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# -------------------------------------------------------------------------
# Database Dependency Type
#
# Creates a database session for each request
# and automatically closes it after the request finishes.
# -------------------------------------------------------------------------

DatabaseSession = Annotated[
    Session,
    Depends(get_db)
]


# -------------------------------------------------------------------------
# Signup API
#
# POST /auth/signup
#
# Flow:
# Request
# → Pydantic validation
# → Check email
# → Hash password
# → Save user in PostgreSQL
# → Return created user
# -------------------------------------------------------------------------

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def signup_user(
    data: SignupRequest,
    db: DatabaseSession
):
    """
    Creates a new ProcureMind user.
    """

    existing_user = get_user_by_email(
        db,
        data.email
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    secure_password = hash_password(
        data.password
    )

    new_user = create_user(
        db=db,
        name=data.name,
        email=data.email,
        hashed_password=secure_password,
        role=data.role
    )

    return new_user


# -------------------------------------------------------------------------
# Login API
#
# POST /auth/login
#
# Flow:
# Email + Password
# → Find user
# → Verify account
# → Verify password
# → Generate JWT
# → Return token
# -------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    data: LoginRequest,
    db: DatabaseSession
):
    """
    Authenticates a user and returns a JWT access token.
    """

    user = get_user_by_email(
        db,
        data.email
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )

    password_is_valid = verify_password(
        data.password,
        user.hashed_password
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        {
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )


# -------------------------------------------------------------------------
# Current Logged-In User API
#
# GET /auth/me
#
# Purpose:
# Returns details of the currently logged-in user
# using the JWT access token.
#
# Flow:
# JWT Token
# → get_current_user()
# → Verify token
# → Find user in PostgreSQL
# → Return user profile
# -------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse
)
def get_current_user_profile(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
):
    """
    Returns information about the currently authenticated user.
    """

    return current_user