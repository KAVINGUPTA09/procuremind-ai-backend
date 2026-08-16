"""
===========================================================================
File: user_crud.py

Project: ProcureMind AI

Purpose:
--------
Handles database operations related to users.

CRUD:
-----
Create -> New user save karna
Read   -> User find karna
Update -> User data change karna
Delete -> User remove karna
===========================================================================
"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User
from app.database.models import User


# -------------------------------------------------------------------------
# Create User
# -------------------------------------------------------------------------

def create_user(
    db: Session,
    name: str,
    email: str,
    hashed_password: str,
    role: str = "buyer"
) -> User:
    """
    Creates and saves a new user in PostgreSQL.
    """

    new_user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role=role
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return new_user


# -------------------------------------------------------------------------
# Get User By ID
# -------------------------------------------------------------------------

def get_user_by_id(
    db: Session,
    user_id: int
) -> User | None:
    """
    Finds one user using the user's ID.
    """

    statement = select(User).where(
        User.id == user_id
    )

    result = db.execute(
        statement
    )

    return result.scalar_one_or_none()


# -------------------------------------------------------------------------
# Get User By Email
# -------------------------------------------------------------------------

def get_user_by_email(
    db: Session,
    email: str
) -> User | None:
    """
    Finds one user using the user's email address.
    """

    statement = select(User).where(
        User.email == email
    )

    result = db.execute(
        statement
    )

    return result.scalar_one_or_none()


# -------------------------------------------------------------------------
# Get All Users
# -------------------------------------------------------------------------

def get_all_users(
    db: Session
) -> list[User]:
    """
    Returns all users stored in the database.
    """

    statement = select(User).order_by(
        User.id
    )

    result = db.execute(
        statement
    )

    return list(
        result.scalars().all()
    )


# -------------------------------------------------------------------------
# Update User
# -------------------------------------------------------------------------

def update_user(
    db: Session,
    user_id: int,
    name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None
) -> User | None:
    """
    Updates selected user fields.
    """

    user = get_user_by_id(
        db,
        user_id
    )

    if user is None:
        return None

    if name is not None:
        user.name = name

    if role is not None:
        user.role = role

    if is_active is not None:
        user.is_active = is_active

    db.commit()

    db.refresh(user)

    return user


# -------------------------------------------------------------------------
# Delete User
# -------------------------------------------------------------------------

def delete_user(
    db: Session,
    user_id: int
) -> bool:
    """
    Deletes one user using the user's ID.
    """

    user = get_user_by_id(
        db,
        user_id
    )

    if user is None:
        return False

    db.delete(user)

    db.commit()

    return True