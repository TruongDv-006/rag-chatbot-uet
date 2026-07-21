import os
from qdrant_client import  QdrantClient


class SemanticRetriever:
    client: QdrantClient

    def __init__(self, qdrant_url = None, collection_name = "uet_handbook"):
        if isinstance(qdrant_url, QdrantClient):
            self.client = qdrant_url
        else:
            if qdrant_url is None:
                qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
    

    def search(self, query_vector, top_k=5):
        if not query_vector:
            return []
        try:
            if hasattr(self.client, 'query_points'):
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    limit=top_k
                )
                search_result = res.points
            else:
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k
                )
        except Exception as e:
            print(f"[SemanticRetriever Error] {e}")
            return []
        results = []
        for hit in search_result:
            results.append({
                "doc_id" : hit.id,
                "content": hit.payload.get("text_content",""),
                "source": hit.payload.get("source",""),
                "score": hit.score
            })

        return results