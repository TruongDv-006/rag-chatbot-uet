from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
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

@router.get("/sessions")
def get_chat_history_bar(
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
    current_user: str = Depends(get_current_user)
):
    """Lấy toàn bộ danh sách phiên chat cũ của sinh viên đem ra Sidebar"""
    return service.get_user_sessions(db=db, username=current_user)

@router.get("/sessions/{session_id}/messages")
def get_messages_of_session(
    session_id: int,
    db: Session = Depends(get_db),
    service: ChatService = Depends(get_chat_service),
    current_user: str = Depends(get_current_user)
):
    """Khi sinh viên bấm vào 1 dòng ở Sidebar, cổng này sẽ tải lại toàn bộ nội dung chat cũ"""
    result = service.get_session_messages(db=db, username=current_user, session_id=session_id)

    # Nếu báo lỗi bảo mật
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])

    return result