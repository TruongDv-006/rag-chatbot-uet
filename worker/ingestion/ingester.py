import os
import uuid
import json
from worker.ingestion.chunker import master_chunk
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECTION_NAME = "uet_handbook"
MODEL_NAME = "BAAI/bge-m3"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

embed_model = SentenceTransformer(MODEL_NAME)
qdrant = QdrantClient(url=QDRANT_URL)

def ensure_collection_exists():
    if not qdrant.collection_exists(collection_name=COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )

def reset_and_ensure_collection():
    if qdrant.collection_exists(collection_name=COLLECTION_NAME):
        qdrant.delete_collection(collection_name=COLLECTION_NAME)
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
    )

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

    # Lay toan bo noi dung cua file 
    texts = [chunk["text"] for chunk in chunks] 
    # Embedding sang vector so
    embeddings = embed_model.encode(texts)
    
    points = []
    for i, chunk in enumerate(chunks):
        point_payload = chunk["metadata"].copy()
        point_payload["text_content"] = chunk["text"]

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embeddings[i].tolist(),
            payload=point_payload 
        )
        points.append(point)
    
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

def ingest_all(force: bool = False):
    ensure_collection_exists()

    force_env = os.getenv("FORCE_INGEST", "false").lower() == "true"
    if not force and not force_env:
        try:
            info = qdrant.get_collection(collection_name=COLLECTION_NAME)
            if info.points_count and info.points_count > 0:
                print(f"[Ingestion] Collection '{COLLECTION_NAME}' đã có {info.points_count} vectors. Bỏ qua re-chunking/ingestion!")
                return
        except Exception as e:
            print(f"[Ingestion] Lỗi khi kiểm tra dữ liệu cũ: {e}")

    print("[Ingestion] Bắt đầu nạp lại dữ liệu vào Qdrant...")
    reset_and_ensure_collection()
    # Đường dẫn quét file thô từ máy local của bạn
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

    print("\n[Hoàn thành] Dữ liệu đã được nạp trực tiếp vào Docker Volume thông qua Qdrant API!")

if __name__ == "__main__":
    ingest_all()