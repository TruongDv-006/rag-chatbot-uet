# pyrefly: ignore[missing-import]
from typing import Any, cast
from sentence_transformers import CrossEncoder

class ReRanker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model = CrossEncoder(model_name)

    def __call__(self, query: str, documents: list[dict], top_k: int = 5):
        return self.rerank(query, documents, top_k)

    def rerank(self, query: str, documents: list[dict], top_k: int = 5):
        """
        Tái xếp hạng danh sách documents dựa trên query
        documents: List các chunk sau khi đi qua bộ RRF
        """
        if not documents:
            return []
        # Tạo ra các cặp đầu vào cho Cross-Encoder (query, text)
        pairs: list[tuple[str, str]] = [(query, str(doc.get("content", ""))) for doc in documents]

        scores = self.model.predict(cast(Any, pairs))

        for i, score in enumerate(scores):
            documents[i]["rerank_score"] = float(score)

        sorted_documents = sorted(documents, key=lambda x:x["rerank_score"], reverse=True)
        
        return sorted_documents[:top_k]