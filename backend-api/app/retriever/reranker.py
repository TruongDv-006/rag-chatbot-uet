# pyrefly: ignore[missing-import]
from setence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name : str = "BAAI/bge-reranker-base"):
        self.model = CrossEncoder(model_name)


    def rerank(self, query: str, documents :list[dict], top_k:int=5):

        pass

