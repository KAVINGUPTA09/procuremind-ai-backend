from app.services.auth_service import (
    create_access_token,
    verify_access_token
)


payload = {

    "sub": "guptakavin6@gmail.com.com",

    "role": "admin"

}

token = create_access_token(
    payload
)

print("\nGenerated JWT Token:\n")

print(token)

decoded = verify_access_token(
    token
)

print("\nDecoded Payload:\n")

print(decoded)