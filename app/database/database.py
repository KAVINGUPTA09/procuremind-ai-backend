import os
from collections.abc import Generator
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import(
    Session,sessionmaker,DeclarativeBase
)

load_dotenv()
Database_URL = os.getenv("DATABASE_URL")

if not Database_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

engine=create_engine(
    Database_URL,
    echo=False,
    pool_pre_ping=True
)

SessionLocal=sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

def get_db()->Generator[Session,None,None]:
    databasesession=SessionLocal()
    try:
        yield databasesession

    finally:
        databasesession.close()








#.env
#   │
#   ▼
#Database Address
 #  │
  # ▼
#Engine (Main Gate)
 #  │
  # ▼
#Session (Token)
 #  │
  # ▼
#Database Work
   #│
  # ▼
#Session Close