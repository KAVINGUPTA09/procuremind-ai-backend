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
7. Authenticate users with Google Sign-In.

Important:
----------
/auth/signup, /auth/login and /auth/google are public endpoints.

/auth/me is protected and requires a valid JWT token.
===========================================================================
"""

import os
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from pydantic import BaseModel
from sqlalchemy.orm import Session

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

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


# =========================================================
# AUTHENTICATION ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================================================
# DATABASE SESSION
# =========================================================

DatabaseSession = Annotated[
    Session,
    Depends(get_db)
]


# =========================================================
# GOOGLE LOGIN REQUEST MODEL
# =========================================================

class GoogleLoginRequest(BaseModel):
    credential: str


# =========================================================
# SIGNUP
# POST /auth/signup
# =========================================================

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
        role="buyer"
    )

    return new_user


# =========================================================
# LOGIN
# POST /auth/login
# =========================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    data: LoginRequest,
    db: DatabaseSession
):
    """
    Authenticates a user using email and password.
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


# =========================================================
# GOOGLE LOGIN
# POST /auth/google
# =========================================================

@router.post(
    "/google",
    response_model=TokenResponse
)
def google_login(
    data: GoogleLoginRequest,
    db: DatabaseSession
):
    """
    Authenticates a user using Google Sign-In.

    Flow:
    Google credential
        ↓
    Verify credential with Google
        ↓
    Get verified email
        ↓
    Existing user? -> use existing account
        ↓
    New user? -> create buyer account
        ↓
    Generate ProcureMind JWT
    """

    google_client_id = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    if not google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication is not configured."
        )

    try:
        google_user = id_token.verify_oauth2_token(
            data.credential,
            google_requests.Request(),
            google_client_id
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential."
        )

    email = google_user.get(
        "email"
    )

    name = google_user.get(
        "name",
        "Google User"
    )

    email_verified = google_user.get(
        "email_verified",
        False
    )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email was not provided."
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email could not be verified."
        )

    user = get_user_by_email(
        db,
        email
    )

    # -----------------------------------------------------
    # First Google login
    # Create account automatically
    # -----------------------------------------------------

    if user is None:

        random_password = str(
            uuid.uuid4()
        )

        secure_password = hash_password(
            random_password
        )

        user = create_user(
            db=db,
            name=name,
            email=email,
            hashed_password=secure_password,
            role="buyer"
        )

    # -----------------------------------------------------
    # Account status check
    # -----------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )

    # -----------------------------------------------------
    # Generate ProcureMind JWT
    # -----------------------------------------------------

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


# =========================================================
# CURRENT USER PROFILE
# GET /auth/me
# =========================================================

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