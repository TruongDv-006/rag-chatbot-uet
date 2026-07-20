import os
from sqlalchemy import create_engine # pyrefly: ignore
from sqlalchemy.orm import sessionmaker, declarative_base # pyrefly: ignore

DATABASE_URL = os.getenv("DATABASE_URL","postgresql://user:password@localhost:5432/uet_rag_db")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()