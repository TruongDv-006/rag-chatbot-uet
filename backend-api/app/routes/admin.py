from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.admin_service import AdminService # pyrefly: ignore

router = APIRouter()

class UploadRequest(BaseModel):
    file_name:str

@router.post("/upload-doc")
def upload_document(request: UploadRequest, service: AdminService = Depends()):
    task_id = service.queue_docment_processing(request.file_name)

    return {
        "message":"Tài liệu đã được đưa vào hàng đợi",
        "task_id":task_id
    }