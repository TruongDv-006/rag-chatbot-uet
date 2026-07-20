import os
from celery import Celery # pyrefly: ignore
from celery import Task # pyrefly: ignore
from worker.core.document_processor import DocumentProcessor

REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")
celery_app = Celery("rag_worker", broker=REDIS_URL, backend=REDIS_URL)

class DocumentIngestionTask(Task):
    name = "worker.tasks.DocumentIngestionTask"

    def run (self, file_path:str, *args, **kwargs):
        """
        Hàm run() đóng vai trò là logic chính của Task
        Celery sẽ tự động gọi hàm này khi có task mới trong hàng đợi
        """
        try:
            file_name = os.path.basename(file_path)
            processor = DocumentProcessor()
            success = processor.process_and_load(file_path=file_path)

            if success:
                print(f"[Worker Class] Xử lý tài liệu {file_name} thành công hoàn toàn!")
                return {"status": "success", "file_name": file_name}
            
            print(f"[Worker Class] Xử lý tài liệu {file_name} thất bại.")
            return {"status": "failed", "error": "Processing failed"}
        except Exception as e:
            print(f"[Worker Class] Lỗi nghiêm trọng khi thực thi task: {e}")
            return {"status": "error", "error": str(e)}

celery_app.register_task(DocumentIngestionTask())