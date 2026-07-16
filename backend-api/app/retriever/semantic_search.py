import os
from qdrant_client import  QdrantClient


class SemanticRetriever:
    client: QdrantClient

    def __init__(self, qdrant_url = None, collection_name = "uet_handbook"):
        if qdrant_url is None :
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
    

    def search(self, query_vector, top_k=5):
        search_result = self.client.search( # pyrefly: ignore
            collection_name=self.collection_name,
            query_vector = query_vector,
            limit = top_k
        )
        results = []
        for hit in search_result:
            results.append({
                "doc_id" : hit.id,
                "content": hit.payload.get("text_content",""),
                "score": hit.score
            })

        return results