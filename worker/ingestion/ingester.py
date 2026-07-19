import os
import uuid
import json
from worker.ingestion.chunker import master_chunk
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# QDRANT_DATA_PATH = os.path.abspath(
#     os.path.join(CURRENT_DIR, "../../infrastructure/volumes/qdrant_data")
# )
# QDRANT_URL = "http://localhost:6333"
# QDRANT_URL = "http://qdrand_db:6333"
COLLECTION_NAME = "uet_handbook"
MODEL_NAME = "BAAI/bge-m3"
QDRANT_URL=os.getenv("QDRANT_URL","http://localhost:6333")
embed_model = SentenceTransformer(MODEL_NAME)
# qdrant = QdrantClient(url=QDRANT_URL)
qdrant = QdrantClient(path=QDRANT_URL)

if not qdrant.collection_exists(collection_name=COLLECTION_NAME):
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )

def process_and_ingest(file_content, filename, folder_type):
    chunks = master_chunk(file_content, filename, folder_type)

    if not chunks:
        print("Khong co du lieu de xu ly")
        return
    #Lay toan bo noi dung cua file 
    texts = [chunk["text"] for chunk in chunks] 
    #Embedding sang vector so
    embeddings = embed_model.encode(texts)
    
    points=[]
    for i, chunk in enumerate(chunks):
        point_payload = chunk["metadata"].copy()
        point_payload["text_content"] = chunk["text"]

        point = PointStruct(
            id = str(uuid.uuid4()),
            vector = embeddings[i].tolist(),
            payload = point_payload 
        )
        points.append(point)
    
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points = points
    )
if __name__ == "__main__":
    # Đường dẫn quét file thô từ máy local của bạn
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    base_dir = "../../infrastructure/volumes/minio_data"
    
    # 1. Quét thư mục docs_parsed
    docs_dir = os.path.abspath(os.path.join(CURRENT_DIR, base_dir, "docs_parsed"))
    if os.path.exists(docs_dir):
        print(f"Đang quét thư mục: {docs_dir}")
        for fname in os.listdir(docs_dir):
            fpath = os.path.join(docs_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    process_and_ingest(f.read(), fname, "docs_parsed")

    # 2. Quét thư mục raw_web
    web_dir = os.path.abspath(os.path.join(CURRENT_DIR, base_dir, "raw_web"))
    if os.path.exists(web_dir):
        print(f"Đang quét thư mục: {web_dir}")
        for fname in os.listdir(web_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(web_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    process_and_ingest(f.read(), fname, "raw_web")

    # ĐÃ SỬA: Khi dùng kết nối mạng (url), QdrantClient tự quản lý connection pool.
    # Bạn không cần gọi qdrant.close() nữa (hàm close chỉ dùng khi kết nối bằng path vật lý).
    print("\n[Hoàn thành] Dữ liệu đã được nạp trực tiếp vào Docker Volume thông qua Qdrant API!")