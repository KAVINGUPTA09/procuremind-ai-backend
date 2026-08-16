from app.database.database import (
    Base,
    engine
)

from app.database import models


print("Creating database tables...")

Base.metadata.create_all(
    bind=engine
)

print("Tables created successfully!")