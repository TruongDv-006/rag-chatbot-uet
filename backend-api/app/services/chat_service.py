from qdrant_client.grpc import Range
import os
import requests
from qdrant_client import QdrantClient
from app.retriever.hybrid import HybridRetrieve # pyrefly: ignore
from app.generation.llm_client import OpenAICompatibleClient # pyrefly: ignore
from app.generation.orchestrator import RAGGenerator # pyrefly: ignore

class ChatService:
    def __init__(self):
        qdrant_url = os.getenv("QDRANT_URL","http://qdrant_db:6333")

        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = "uet_handbook"
        self.embed_model = "bge-m3"
        self.llm_url = os.getenv("LLM_API_BASE","http://ollama:11434/api")

        self.retriever = HybridRetrieve(
            self.qdrant_client,
            self.collection_name,
            self.embed_model
        )

        self.llm_client = OpenAICompatibleClient()
        self.generator = RAGGenerator(self.llm_client)


    def _get_embedding(self, text:str):
        embed_url = f"{self.llm_client}/embeddings"

        response = requests.post(embed_url, json={
            "model" : self.embed_model,
            "prompt": text
        })
        return response.json().get("embedding",[])


    def process_message(self, message:str):
        try:
            # Embedding câu hỏi thành vector
            query_vector = self._get_embedding(message)
            #
            retrieved_docs = self.retriever.search(
                query = message,
                query_vector = query_vector,
                top_k=5
            )

            #
            score_threshold = 0.6
            reply_text = self.generator.execute(
                query = message,
                retrieved_docs=retrieved_docs,
                score_threshold=score_threshold
            )

            #
            valid_docs = [doc for doc in retrieved_docs if doc.get("score",0.0) >= score_threshold]
            mapped_sources = {}

            for index, doc in enumerate(valid_docs, start=1):
                mapped_sources[str(index)]=doc.get("source","Sổ tay UET")
            return {
                "reply":reply_text,
                "source":mapped_sources
            }
        except Exception as e:
            return {"rely":"Hệ thống đang gặp lỗi sự cố: {str(e)}", "source":[]}

