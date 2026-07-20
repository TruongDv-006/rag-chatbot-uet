# pyrefly: ignore [missing-import]
from celery import Celery
import os

class AdminService:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis_broker:6379/0")
        self.queue_client = Celery("uet_backend_api", broker = redis_url)

    def queue_docment_processing(self, file_name:str):
        """
        Hàm này nhận file tài liệu rồi đẩy nó vào hàng đợi Redis
        Sau đó gửi task có tên là worker.tasks.DocumentIngestionTask vào Redis
        args = [file_name] là dữ liệu gửi kèm cho Worker
        """

        task = self.queue_client.send_task(
            "worker.tasks.DocumentIngestionTask",
            args = [file_name]
        )

        return task.id


# # app/routes/chat.py
# from fastapi import APIRouter, Depends
# from app.utils.security import get_current_user # Nhập Bác bảo vệ vào

# @router.post("/chat")
# def chat_with_rag(
#     request: ChatRequest, 
#     service: ChatService = Depends(get_chat_service),
#     # CHỈ CẦN THÊM DÒNG NÀY: Bác bảo vệ sẽ tự động chặn hoặc cho qua
#     current_user_email: str = Depends(get_current_user) 
# ):
#     # Khách đã lọt được vào đây nghĩa là Token xịn 100%
#     print(f"Sinh viên {current_user_email} vừa hỏi: {request.message}")
    
#     return service.process_message(request.message)
