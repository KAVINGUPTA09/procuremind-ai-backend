from sqlalchemy import text

from app.database.database import engine

try:

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT version();")
        )

        print("\nConnection Successful!\n")

        print(result.scalar())

except Exception as error:

    print("\nConnection Failed!\n")

    print(error)