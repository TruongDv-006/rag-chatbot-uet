from functools import lru_cache
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.chat_service import ChatService # pyrefly: ignore

router = APIRouter()
class ChatRequest(BaseModel):
    message:str
    
@lru_cache()
def get_chat_service():
    return ChatService()

@router.post("/chat")
def chat_with_rag(request: ChatRequest, service: ChatService=Depends(get_chat_service)):
    return service.process_message(request.message)