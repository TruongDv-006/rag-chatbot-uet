# worker/tasks.py
import os
from celery import Celery # pyrefly: ignore
from worker.core.document_processor import DocumentProcessor

# 🔥 ĐÃ SỬA: Chuỗi dự phòng mặc định sẽ trỏ tới container redis_broker nếu chạy trong mạng Docker
REDIS_URL = os.getenv("REDIS_URL", "redis://redis_broker:6379/0")
celery_app = Celery("rag_worker", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(name="tasks.process_document_task")
def process_document_task(file_path: str, file_name: str, document_id: str):
    """
    Task chạy ngầm để đọc file, chia đoạn và đẩy vào Qdrant Vector DB
    """
    print(f"[Worker] Bắt đầu xử lý tài liệu: {file_name} (ID: {document_id})")
    
    try:
        processor = DocumentProcessor()
        success = processor.process_and_load(
            file_path=file_path, 
            file_name=file_name, 
            document_id=document_id
        )
        
        if success:
            print(f"[Worker] Xử lý tài liệu {file_name} thành công 100%!")
            return {"status": "success", "document_id": document_id}
        else:
            print(f"[Worker] Xử lý tài liệu {file_name} thất bại.")
            return {"status": "failed", "error": "Processing failed"}
            
    except Exception as e:
        print(f"[Worker] Lỗi nghiêm trọng khi chạy task: {e}")
        return {"status": "error", "error": str(e)}