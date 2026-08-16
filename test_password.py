from app.services.security_service import (
    hash_password,
    verify_password
)


password = "Kavin@1494"

hashed_password = hash_password(
    password
)

print("Original Password:", password)
print("Hashed Password:", hashed_password)

correct_result = verify_password(
    password,
    hashed_password
)

wrong_result = verify_password(
    "WrongPassword123",
    hashed_password
)

print("Correct Password Match:", correct_result)
print("Wrong Password Match:", wrong_result)