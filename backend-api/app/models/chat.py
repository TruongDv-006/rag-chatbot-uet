from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text # pyrefly:ignore
from sqlalchemy import relationship # pyrefly:ignore
from app.core.database import Base # pyrefly:ignore

class ChatSession(Base):
    __tablename__="chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable = False, default= "Đoạn chat mới")
    created_at = Column(DateTime, default = lambda: datetime.now(timezone.utc))
    user_id = Colume(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    id = Column(Integer, primary_key=True, index=True)

    role=Column(String, nullable=False)
    content= Column(Text, nullable=False)
    created_at = Column(DateTime, default= lambda: datetime.now(timezone.utc))
    
    session_id=Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    session = relationship("ChatSession", back_populates="messages")