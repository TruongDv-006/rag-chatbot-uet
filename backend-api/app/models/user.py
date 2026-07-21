from sqlalchemy import Integer, Column, String, DateTime, func # pyrefly: ignore
from app.core.database import Base # pyrefly: ignore

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username=Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique = True, index = True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())