from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.admin_service import AdminService # pyrefly: ignore
from app.utils.security import get_current_admin # pyrefly:ignore

router = APIRouter()

class UploadRequest(BaseModel):
    file_name:str

@router.post("/upload-doc")
def upload_document(request: UploadRequest, service: AdminService = Depends(), current_admin: str = Depends(get_current_admin)):
    print(f"[Admin API] Tài khoản {current_admin} đang đẩy file {request.file_name} vào hàng đợi Celery")
    task_id = service.queue_docment_processing(request.file_name)
    return {
        "message":"Tài liệu đã được đưa vào hàng đợi",
        "task_id":task_id,
        "triggered_by": current_admin
    }