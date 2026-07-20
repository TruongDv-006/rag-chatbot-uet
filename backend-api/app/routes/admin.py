import os   
from fastapi import APIRouter, Depends, UploadFile, File
from app.services.admin_service import AdminService # pyrefly: ignore
from app.utils.security import get_current_admin # pyrefly:ignore

router = APIRouter()

UPLOAD_DIR = "/app/infrastructure/volumes/minio_data/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-doc")
def upload_document(file: UploadFile = File(...), service: AdminService = Depends(), current_admin: str = Depends(get_current_admin)):
    filename = file.filename if file.filename else "unknown_document.pdf"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    task_id = service.queue_docment_processing(file_path)
    return {
        "message":"Tài liệu đã được đưa vào hàng đợi",
        "task_id":task_id,
        "triggered_by": current_admin
    }