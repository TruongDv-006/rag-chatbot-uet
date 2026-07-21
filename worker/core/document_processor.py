import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer 
# Sử dụng trực tiếp hàm băm nhỏ thông minh từ chunker.py theo ý bạn
from worker.ingestion.chunker import master_chunk
from worker.crawler.document_parser import DocumentParser

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
    def process_and_load(self, file_path:str):
        file_name = os.path.basename(file_path)
        # Xử lý file thô (.pdf, .docx) mà người dùng upload lên bằng DocumentParser 
        base_dir = "/app/infrastructure/volumes/minio_data"
        folder_type = "doc_parsed"

        parser = DocumentParser()
        content = ""
        if file_name.lower().endswith(".pdf"):
            raw_text = parser.parse_pdf(file_path = file_path)
        elif file_name.lower().endswith(".docx"):
            raw_text = parser.parse_docx(file_path = file_path)
        else:
            print("Không hỗ trợ định dạng này")
            return False
        
        if not raw_text.strip():
            return False

        base_name = os.path.splitext(file_name)[0]
        parsed_filename = f"{base_name}_parsed.txt"
        save_path = os.path.join(base_dir, "docs_parsed", parsed_filename)
         
        os.makedirs(os.path.dirname(save_path), exist_ok = True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(raw_text)

        # Giai đoạn Chunking (sử dụng file_name gốc để metadata source khớp với doc_name)
        chunks = master_chunk(raw_text, file_name, folder_type)
        if not chunks: 
            return False

        # Tạo vector và lưu vào Qdrant
        document_id = str(uuid.uuid4())
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts)

        points = []
        for idx, chunk in enumerate(chunks):
            point_payload = chunk["metadata"].copy()
            point_payload["text_content"] = chunk["text"]
            point_payload["doc_id"] = document_id

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[idx].tolist(),
                payload=point_payload
            )
            points.append(point)

        try:
            self.qdrant_client.upsert(collection_name=self.collection_name, points=points)
            print(f"[Processor] Thành công. Đã xử lý {len(points)} đoạn từ file {file_name} vào Qdrant.")
            return True
        except Exception as e:
            print(f"[Processor] Lỗi khi đẩy dữ liệu lên Qdrant: {e}")
            return False