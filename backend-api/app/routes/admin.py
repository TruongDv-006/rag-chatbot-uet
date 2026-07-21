import os
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session # pyrefly: ignore
from app.core.database import get_db # pyrefly: ignore
from app.models.user import User # pyrefly: ignore
from app.models.chat import ChatSession # pyrefly: ignore
from app.services.admin_service import AdminService # pyrefly: ignore
from app.utils.security import get_current_admin # pyrefly:ignore

router = APIRouter()

UPLOAD_DIR = "/app/infrastructure/volumes/minio_data/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─────────────────────────────────────────
# POST /upload-doc – Tải tài liệu lên hàng đợi
# ─────────────────────────────────────────
@router.post("/upload-doc")
def upload_document(
    file: UploadFile = File(...),
    service: AdminService = Depends(),
    current_admin: str = Depends(get_current_admin)
):
    filename  = file.filename if file.filename else "unknown_document.pdf"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    task_id = service.queue_docment_processing(file_path)
    return {
        "message":    "Tài liệu đã được đưa vào hàng đợi",
        "task_id":    task_id,
        "triggered_by": current_admin
    }

# ─────────────────────────────────────────
# GET /stats – Thống kê tổng quan dashboard
# ─────────────────────────────────────────
@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    total_users    = db.query(User).count()
    total_sessions = db.query(ChatSession).count()

    # Đếm tài liệu trong thư mục upload
    try:
        docs = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(('.pdf', '.docx'))]
        total_documents = len(docs)
    except Exception:
        total_documents = 0

    return {
        "total_users":     total_users,
        "total_documents": total_documents,
        "total_sessions":  total_sessions,
        "pending_tasks":   0,
        "recent_activity": []
    }

# ─────────────────────────────────────────
# GET /users – Danh sách người dùng
# ─────────────────────────────────────────
@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    users = db.query(User).all()
    result = []
    for u in users:
        session_count = db.query(ChatSession).filter(ChatSession.user_id == u.id).count()
        result.append({
            "id":            u.id,
            "username":      u.username,
            "email":         u.email,
            "full_name":     u.full_name,
            "role":          u.role,
            "session_count": session_count,
            "created_at":    None  # User model chưa có created_at
        })
    return result

# ─────────────────────────────────────────
# GET /documents – Danh sách tài liệu đã upload
# ─────────────────────────────────────────
@router.get("/documents")
def get_documents(
    current_admin: str = Depends(get_current_admin)
):
    try:
        docs = []
        for i, fname in enumerate(os.listdir(UPLOAD_DIR)):
            if fname.endswith(('.pdf', '.docx')):
                fpath = os.path.join(UPLOAD_DIR, fname)
                fsize = os.path.getsize(fpath)
                ftype = "PDF" if fname.endswith('.pdf') else "DOCX"
                docs.append({
                    "id":          i + 1,
                    "filename":    fname,
                    "file_type":   ftype,
                    "file_size":   fsize,
                    "status":      "processed",
                    "created_at":  None
                })
        return docs
    except Exception as e:
        return []

# ─────────────────────────────────────────
# DELETE /documents/{doc_id} – Xóa tài liệu
# ─────────────────────────────────────────
@router.delete("/documents/{doc_name}")
def delete_document(
    doc_name: str,
    current_admin: str = Depends(get_current_admin)
):
    file_path = os.path.join(UPLOAD_DIR, doc_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": f"Đã xóa tài liệu: {doc_name}"}
    return {"message": "Không tìm thấy tài liệu"}

# ─────────────────────────────────────────
# GET /tasks – Trạng thái hàng đợi Celery
# ─────────────────────────────────────────
@router.get("/tasks")
def get_tasks(
    service: AdminService = Depends(),
    current_admin: str = Depends(get_current_admin)
):
    try:
        from app.worker.tasks import celery_app # pyrefly: ignore
        inspect = celery_app.control.inspect(timeout=2)
        active  = inspect.active()  or {}
        reserved= inspect.reserved() or {}

        tasks = []
        for worker, task_list in {**active, **reserved}.items():
            for t in task_list:
                tasks.append({
                    "task_id":  t.get("id", ""),
                    "filename": str(t.get("args", ["?"])[0]).split("/")[-1] if t.get("args") else "?",
                    "status":   "STARTED" if worker in active else "PENDING",
                    "worker":   worker,
                    "created_at": None
                })
        return tasks
    except Exception:
        return []