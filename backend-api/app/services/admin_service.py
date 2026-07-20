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

###### Cần cài thêm cái tài khoản admin mặc định

