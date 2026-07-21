from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, admin # pyrefly: ignore
from app.core.database import engine, Base, SessionLocal # pyrefly: ignore
from app.models.user import User # pyrefly: ignore
from app.models.chat import ChatSession, ChatMessage # pyrefly:ignore
from app.routes.auth import router as auth_router # pyrefly: ignore
from app.core.init_db import seed_default_users # pyrefly: ignore

# Tự động tạo bảng nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API RAG Sổ tay UET",
    description="Hệ thống Backend cho Chatbot sinh viên và Phòng đào tạo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["Phòng chat sinh viên"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Trang chủ Admin"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Xác thực và Bảo mật"])

@app.on_event("startup")
def startup_event():
    """Seed tài khoản mặc định khi backend khởi động"""
    db = SessionLocal()
    try:
        seed_default_users(db)
    finally:
        db.close()

@app.get("/")
def heath_check():
    return {"status": "Backend API đang hoạt động ổn định"}