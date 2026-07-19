# worker/core/document_processor.py
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer 

class DocumentProcessor:
    def __init__(self):
        # 🔥 ĐÃ SỬA: Đọc trực tiếp biến QDRANT_URL từ file docker-compose của bạn
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = "uet_handbook"
        
        # 2. Tải mô hình Embedding cục bộ
        self.embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
        # Đảm bảo Collection trong Qdrant đã được khởi tạo
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Tạo collection trên Qdrant nếu chưa có"""
        collections = self.qdrant_client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            # Model bge-small-en-v1.5 trả ra vector 384 chiều
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def _chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
        """Hàm băm nhỏ văn bản dài thành các đoạn nhỏ có gối đầu lên nhau"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - chunk_overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def process_and_load(self, file_path: str, file_name: str, document_id: str) -> bool:
        """Đọc file thô, băm nhỏ, tạo vector và lưu vào Qdrant"""
        if not os.path.exists(file_path):
            print(f"Lỗi: Không tìm thấy file tại đường dẫn {file_path}")
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # 1. Băm nhỏ văn bản
        chunks = self._chunk_text(raw_text)
        if not chunks:
            return False

        points = []
        # 2. Duyệt qua từng đoạn nhỏ để xử lý
        for idx, chunk_content in enumerate(chunks):
            # Biến chữ thành dãy số (Vector)
            vector = self.embedding_model.encode(chunk_content).tolist()
            
            # Tạo ID duy nhất cho từng point trong Qdrant
            point_id = f"{document_id}_{idx}"
            
            # Đóng gói dữ liệu kèm thông tin nguồn (Source) để sau này RAG trích dẫn
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "doc_id": document_id,
                        "text": chunk_content,
                        "source": file_name, 
                        "chunk_index": idx
                    }
                )
            )

        # 3. Đẩy đồng loạt dữ liệu lên Qdrant Vector DB
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return True