import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session # pyrefly: ignore
from qdrant_client import QdrantClient # pyrefly: ignore
from qdrant_client.models import Filter, FieldCondition, MatchValue # pyrefly: ignore
from app.core.database import get_db # pyrefly: ignore
from app.models.user import User # pyrefly: ignore
from app.models.chat import ChatSession # pyrefly: ignore
from app.services.admin_service import AdminService # pyrefly: ignore
from app.utils.security import get_current_admin, get_password_hash # pyrefly:ignore

router = APIRouter()

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/infrastructure/volumes/minio_data/documents")
PARSED_DIR = os.getenv("PARSED_DIR", "/infrastructure/volumes/minio_data/docs_parsed")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant_db:6333")
COLLECTION_NAME = "uet_handbook"

try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(PARSED_DIR, exist_ok=True)
except Exception:
    pass

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
        docs = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(('.pdf', '.docx'))]
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
            "created_at":    u.created_at.isoformat() if u.created_at else None
        })
    return result

# ─────────────────────────────────────────
# PUT /users/{user_id} – Cập nhật thông tin người dùng
# ─────────────────────────────────────────
@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if data.email and data.email != user.email:
        existing = db.query(User).filter(User.email == data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email này đã được sử dụng bởi tài khoản khác")
        user.email = data.email

    if data.full_name is not None:
        user.full_name = data.full_name

    if data.role is not None:
        if data.role not in ["admin", "student"]:
            raise HTTPException(status_code=400, detail="Vai trò không hợp lệ (chỉ chấp nhận admin hoặc student)")
        user.role = data.role

    if data.password:
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")
        user.hashed_password = get_password_hash(data.password)

    db.commit()
    db.refresh(user)

    session_count = db.query(ChatSession).filter(ChatSession.user_id == user.id).count()
    return {
        "id":            user.id,
        "username":      user.username,
        "email":         user.email,
        "full_name":     user.full_name,
        "role":          user.role,
        "session_count": session_count,
        "created_at":    user.created_at.isoformat() if user.created_at else None
    }

# ─────────────────────────────────────────
# DELETE /users/{user_id} – Xóa người dùng
# ─────────────────────────────────────────
@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if user.username == current_admin:
        raise HTTPException(status_code=400, detail="Bạn không thể tự xóa tài khoản admin đang đăng nhập")

    db.query(ChatSession).filter(ChatSession.user_id == user.id).delete()
    db.delete(user)
    db.commit()

    return {"message": f"Đã xóa người dùng {user.username} thành công"}


# ─────────────────────────────────────────
# GET /documents – Danh sách tài liệu đã upload
# ─────────────────────────────────────────
@router.get("/documents")
def get_documents(
    current_admin: str = Depends(get_current_admin)
):
    try:
        if not os.path.exists(UPLOAD_DIR):
            return []
        docs = []
        for i, fname in enumerate(os.listdir(UPLOAD_DIR)):
            if fname.lower().endswith(('.pdf', '.docx')):
                fpath = os.path.join(UPLOAD_DIR, fname)
                fsize = os.path.getsize(fpath)
                ftype = "PDF" if fname.lower().endswith('.pdf') else "DOCX"
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
# DELETE /documents/{doc_name} – Xóa tài liệu ở cả infrastructure và Qdrant
# ─────────────────────────────────────────
@router.delete("/documents/{doc_name}")
def delete_document(
    doc_name: str,
    current_admin: str = Depends(get_current_admin)
):
    base_name = os.path.splitext(doc_name)[0]
    raw_deleted = False
    
    # 1. Xóa file thô trong thư mục infrastructure
    file_path = os.path.join(UPLOAD_DIR, doc_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        raw_deleted = True

    # Xóa file parsed tương ứng (nếu có)
    parsed_path1 = os.path.join(PARSED_DIR, f"{base_name}_parsed.txt")
    if os.path.exists(parsed_path1):
        os.remove(parsed_path1)

    parsed_path2 = os.path.join(PARSED_DIR, f"{doc_name}_parsed.txt")
    if os.path.exists(parsed_path2):
        os.remove(parsed_path2)

    # 2. Xóa các vectors đã chunking, ingestion trong Qdrant
    qdrant_deleted = False
    try:
        qdrant_client = QdrantClient(url=QDRANT_URL)
        if qdrant_client.collection_exists(COLLECTION_NAME):
            qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    should=[
                        FieldCondition(key="source", match=MatchValue(value=doc_name)),
                        FieldCondition(key="source", match=MatchValue(value=f"{base_name}_parsed.txt")),
                        FieldCondition(key="source", match=MatchValue(value=f"{doc_name}_parsed.txt")),
                        FieldCondition(key="source", match=MatchValue(value=base_name))
                    ]
                )
            )
            qdrant_deleted = True
    except Exception as e:
        print(f"[Delete Document Qdrant Error] {e}")

    if raw_deleted or qdrant_deleted:
        return {"message": f"Đã xóa tài liệu '{doc_name}' ở cả thư mục infrastructure và Qdrant"}
    return {"message": f"Không tìm thấy tài liệu: {doc_name}"}

# ─────────────────────────────────────────
# GET /tasks – Trạng thái hàng đợi Celery
# ─────────────────────────────────────────
@router.get("/tasks")
def get_tasks(
    service: AdminService = Depends(),
    current_admin: str = Depends(get_current_admin)
):
    try:
        inspect = service.queue_client.control.inspect(timeout=2)
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