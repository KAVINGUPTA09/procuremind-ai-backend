import os

from datetime import (
    datetime,
    timedelta,
    timezone
)

from dotenv import load_dotenv

from jose import (
    jwt,
    JWTError
)


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        60
    )
)


if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY not found in .env"
    )


def create_access_token(
    data: dict
) -> str:
    """
    Generates a JWT access token.
    """

    # User data copy
    payload = data.copy()

    # Calculate token expiry time
    expire = (
        datetime.now(timezone.utc)
        +
        timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    # Add expiry inside JWT payload
    payload.update(
        {
            "exp": expire
        }
    )

    # Generate signed JWT token
    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def verify_access_token(
    token: str
) -> dict:
    """
    Verifies and decodes a JWT access token.
    """

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:

        raise ValueError(
            "Invalid or expired token."
        )