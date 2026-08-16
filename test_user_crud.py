from app.crud.user_crud import (
    create_user,
    get_user_by_email,
    get_all_users,
    update_user
)

from app.database.database import SessionLocal


db = SessionLocal()

try:

    existing_user = get_user_by_email(
        db,
        "kavin@example.com"
    )

    if existing_user is None:

        user = create_user(
            db=db,
            name="Kavin Gupta",
            email="kavin@example.com",
            hashed_password="temporary_hashed_password",
            role="buyer"
        )

        print("User created successfully!")
        print("User ID:", user.id)

    else:

        print("User already exists.")
        print("User ID:", existing_user.id)

    users = get_all_users(
        db
    )

    print("\nAll Users:")

    for user in users:
        print(
            user.id,
            user.name,
            user.email,
            user.role,
            user.is_active
        )

    updated_user = update_user(
        db=db,
        user_id=1,
        role="admin"
    )

    if updated_user:
        print(
            "\nUpdated Role:",
            updated_user.role
        )

finally:
    db.close()