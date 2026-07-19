#
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chat, admin # pyrefly: ignore

app = FastAPI(
    title="API RAG Sổ tay UET",
    description = "Hệ thống Backend cho Chatbot sinh viên và Phòng đào tạo",
    version = "1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat.router, prefix = "/api/v1")
app.include_router(admin.router, prefix = "/app/v1/admin")

@app.get("/")
def heath_check():
    return {"status": "Backend API đang hoạt động ổn định"}