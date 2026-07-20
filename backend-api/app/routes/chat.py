from functools import lru_cache
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.chat_service import ChatService # pyrefly: ignore
from app.utils.security import get_current_user # pyrefly: ignore
from sqlalchemy.orm import Session # pyrefly:ignore
from app.core.database import get_db # pyrefly:ignore

router = APIRouter()
class ChatRequest(BaseModel):
    message:str
    session_id: int | None = None
    
@lru_cache()
def get_chat_service():
    return ChatService()

@router.post("/chat")
def chat_with_rag(request: ChatRequest, db: Session = Depends(get_db), service: ChatService=Depends(get_chat_service), current_user: str = Depends(get_current_user)):
    return service.process_message(
        db=db,
        message=request.message, 
        username=current_user,
        session_id=request.session_id
    )