import os
import sys
import uuid
from pathlib import Path

# pyrefly: ignore [missing-import]
from qdrant_client import QdrantClient 
# pyrefly: ignore [missing-import]
from qdrant_client.models import Distance, PointStruct, VectorParams
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer

from worker.ingestion.chunker import master_chunk

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[2]
COLLECTION_NAME = "uet_handbook"
MODEL_NAME = "BAAI/bge-m3"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DATA_ROOT = REPO_ROOT / "infrastructure" / "volumes" / "minio_data"


def _ensure_collection(qdrant: QdrantClient) -> None:
    if not qdrant.collection_exists(collection_name=COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )


def process_and_ingest(qdrant: QdrantClient, embed_model: SentenceTransformer, file_content: str, filename: str, folder_type: str) -> int:
    chunks = master_chunk(file_content, filename, folder_type)
    if not chunks:
        return 0

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_model.encode(texts, batch_size=32, show_progress_bar=False)

    points = []
    for i, chunk in enumerate(chunks):
        point_payload = chunk["metadata"].copy()
        point_payload["text_content"] = chunk["text"]

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i].tolist(),
                payload=point_payload,
            )
        )

    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def ingest_all() -> bool:
    print("=" * 70)
    print("INGESTION SCRIPT")
    print("=" * 70)

    print("\n[1/5] Connecting to Qdrant...")
    try:
        qdrant = QdrantClient(url=QDRANT_URL)
        _ensure_collection(qdrant)
        info = qdrant.get_collection(COLLECTION_NAME)
        print(f"✓ Connected. Current points: {info.points_count}")
    except Exception as exc:
        print(f"✗ Error: {exc}")
        return False

    print("\n[2/5] Loading embedding model (this may take 1-2 mins)...")
    try:
        print(f"  Loading {MODEL_NAME}...")
        embed_model = SentenceTransformer(MODEL_NAME)
        print("✓ Model loaded successfully")
    except Exception as exc:
        print(f"✗ Error loading model: {exc}")
        return False

    _ensure_collection(qdrant)

    total_points = 0

    docs_dir = DATA_ROOT / "docs_parsed"
    web_dir = DATA_ROOT / "raw_web"

    print("\n[3/5] Scanning documents...")
    if docs_dir.exists():
        txt_files = sorted(docs_dir.glob("*.txt"))
        print(f"✓ Found {len(txt_files)} files:")
        for f in txt_files:
            mb = f.stat().st_size / 1024 / 1024
            print(f"    • {f.name} ({mb:.1f} MB)")

        print("\n[4/5] Processing docs_parsed...")
        print("(This will take several minutes on CPU)...\n")
        for file_idx, fpath in enumerate(txt_files, 1):
            print(f"  [{file_idx}/{len(txt_files)}] {fpath.name}...", end="", flush=True)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                points_count = process_and_ingest(qdrant, embed_model, content, fpath.name, "docs_parsed")
                total_points += points_count
                print(f" [{points_count} points] ✓")
            except Exception as exc:
                print(f" [ERROR: {str(exc)[:40]}]")

    if web_dir.exists():
        json_files = sorted(web_dir.glob("*.json"))
        if json_files:
            print(f"\n✓ Found {len(json_files)} raw_web files")
            print("\n[4/5] Processing raw_web...")
        for file_idx, fpath in enumerate(json_files, 1):
            print(f"  [{file_idx}/{len(json_files)}] {fpath.name}...", end="", flush=True)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                points_count = process_and_ingest(qdrant, embed_model, content, fpath.name, "raw_web")
                total_points += points_count
                print(f" [{points_count} points] ✓")
            except Exception as exc:
                print(f" [ERROR: {str(exc)[:40]}]")

    print("\n[5/5] Verifying...")
    try:
        info = qdrant.get_collection(COLLECTION_NAME)
        print(f"✓ Total points in Qdrant: {info.points_count}")
        print(f"  Expected from this run: {total_points}")
    except Exception:
        pass

    print("\n" + "=" * 70)
    print("✓ INGESTION COMPLETE")
    print("=" * 70)
    return True


if __name__ == "__main__":
    sys.exit(0 if ingest_all() else 1)