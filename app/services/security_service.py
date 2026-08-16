"""
===========================================================================
File: security_service.py

Purpose:
--------
Securely hashes and verifies user passwords using Argon2.
===========================================================================
"""

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(
    password: str
) -> str:
    """
    Converts a plain password into a secure Argon2 hash.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    return password_hash.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Checks whether a plain password matches
    the stored Argon2 password hash.
    """

    if not plain_password or not hashed_password:
        return False

    return password_hash.verify(
        plain_password,
        hashed_password
    )