# pyrefly: ignore[missing-import]
from typing import Any, cast
# pyrefly: ignore [missing-import]
from sentence_transformers import CrossEncoder
# pyrefly: ignore [missing-import]
import torch
class ReRanker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        self._model = None
        self._load_failed = False

    def _get_model(self):
        if self._model is None and not self._load_failed:
            try:
                self._model = CrossEncoder(self.model_name, device="cuda" if torch.cuda.is_available() else "cpu")
            except Exception as e:
                print(f"[ReRanker Warning] Không tải được model rerank {self.model_name}: {e}")
                self._load_failed = True
        return self._model

    def __call__(self, query: str, documents: list[dict], top_k: int = 3):
        return self.rerank(query, documents, top_k)

    def rerank(self, query: str, documents: list[dict], top_k: int = 3):
        if not documents:
            return []
        model = self._get_model()
        if model is None:
            return documents[:top_k]
        try:
            pairs: list[tuple[str, str]] = [(query, str(doc.get("content", ""))) for doc in documents]
            scores = model.predict(cast(Any, pairs))

            for i, score in enumerate(scores):
                documents[i]["rerank_score"] = float(score)
                documents[i]["score"] = float(score)

            sorted_documents = sorted(documents, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return sorted_documents[:top_k]
        except Exception as e:
            print(f"[ReRanker Error] {e}")
            return documents[:top_k]