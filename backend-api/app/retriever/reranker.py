import math
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
        # Chỉ rerank tối đa 5 candidate tốt nhất để tối ưu tốc độ xử lý 
        candidate_docs = documents[:5]
        try:
            pairs: list[tuple[str, str]] = [(query, str(doc.get("content", ""))) for doc in candidate_docs]
            scores = model.predict(cast(Any, pairs))

            for i, score in enumerate(scores):
                # Chuẩn hóa logit bằng hàm Sigmoid
                sigmoid_score = 1.0 / (1.0 + math.exp(-float(score)))
                candidate_docs[i]["rerank_score"] = sigmoid_score
                candidate_docs[i]["score"] = sigmoid_score

            sorted_documents = sorted(candidate_docs, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            return sorted_documents[:top_k]
        except Exception as e:
            print(f"[ReRanker Error] {e}")
            return documents[:top_k]