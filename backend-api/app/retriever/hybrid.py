# pyrefly: ignore [missing-import]
from qdrant_client import QdrantClient
from app.retriever.semantic_search import SemanticRetriever # pyrefly: ignore[missing-import]
from app.retriever.keyword_search import KeywordRetriever # pyrefly: ignore[missing-import]
from app.retriever.rank_fusion import RankFusion # pyrefly: ignore[missing-import]
from app.retriever.reranker import ReRanker # pyrefly: ignore[missing-import]


class HybridRetrieve:

    def __init__(self,qdrant_client : QdrantClient, collection_name: str, embed_model):
        self.qdrant_client=qdrant_client

        self.collection_name=collection_name

        self.semantic_retriever = SemanticRetriever(
            qdrant_url=qdrant_client,
            collection_name=collection_name
        ) 
        document = self._scroll_all_documents_from_qdrant()
        self.keyword_retriever = KeywordRetriever(
            documents = document
        )
        self.rank_fusion = RankFusion(k=60)
        self.reranker = ReRanker(model_name = "BAAI/bge-reranker-base")

    def _scroll_all_documents_from_qdrant(self):
        """
        Hàm này dùng để kéo toàn bộ tài liệu từ qdrant về để làm tham số cho các phần sau xử lý
        """        
        documents = []
        next_page_offset = None
        try:
            if not self.qdrant_client.collection_exists(self.collection_name):
                return documents
        except Exception:
            return documents

        try:
            while True:
                respone, next_page_offset = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    with_payload = True,
                    with_vectors=False,
                    offset=next_page_offset
                )
                for point in respone:
                    payload = point.payload if point.payload else {}
                    documents.append({
                        "doc_id": str(point.id),
                        "content": str(payload.get("text_content","")),
                        "source": str(payload.get("source",""))
                    })
                if next_page_offset is None:
                    break
        except Exception as e:
            print(f"[HybridRetrieve Scroll Warning] {e}")

        return documents

    def search(self, query:str, query_vector:list[float], top_k: int=5):
        raw_top_k = top_k * 2 

        semantic_result = self.semantic_retriever.search(
            query_vector,
            raw_top_k
        )

        keyword_result = self.keyword_retriever.search(
            query,
            raw_top_k
        )

        fused_result = self.rank_fusion.reciprocal_rank_fusion(
            semantic_result,
            keyword_result
        )

        final_reranked_result = self.reranker(
            query,
            fused_result,
            top_k
        )

        return final_reranked_result