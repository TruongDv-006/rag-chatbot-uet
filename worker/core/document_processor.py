import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer 
# Sử dụng trực tiếp hàm băm nhỏ thông minh từ chunker.py theo ý bạn
from worker.ingestion.chunker import master_chunk

class DocumentProcessor:
    def __init__(self):
        # 1. Cấu hình kết nối mạng Qdrant (Chuẩn để chạy trong Docker)
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = "uet_handbook"
        
        # 2. Khởi tạo mô hình tạo Vector BAAI/bge-m3 (đầu ra 1024 chiều)
        self.embedding_model = SentenceTransformer("BAAI/bge-m3")
        
        # 3. Tự động kiểm tra và tạo Collection trên Qdrant nếu chưa có
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Tạo collection trên Qdrant nếu chưa tồn tại"""
        if not self.qdrant_client.collection_exists(collection_name=self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )
    def process_and_load(self, file_name:str):
        pass

        