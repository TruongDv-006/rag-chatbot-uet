from rank_bm25 import BM25Okapi
from underthesea import word_tokenize


class KeywordRetriever:

    def __init__(self, documents: list):
        """
        documents: Danh sách các chunk thô được lấy từ các phần tử trong qdrant
        Mỗi phần tử có cấu trúc như sau:(cái này tự định nghĩa)
        {
        "doc_id": uuid,
        "content": payload["text_content"],
        "source": payload["source"]
        }
        """
        self.documents = documents
        
        tokenized_corpus = []
        for doc in self.documents:
            #Chuan hoa lai van ban thanh chu thuong
            text = doc["content"].lower()
            #Tach tu tieng viet theo ngu nghia voi underthesea
            segmented_text = str(word_tokenize(text, format = "text"))
            #Cat chuoi bang khoang trang thanh mang cac tu ghep
            tokenized_corpus.append(segmented_text.split(" "))
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, top_k :int=5):
        segmented_query = str(word_tokenize(query,format="text"))
        tokenized_query = segmented_query.split(" ")

        #Lay diem cac doan van ban trong kho
        doc_scores = self.bm25.get_scores(tokenized_query)
        #Sap xep giam dan cac index cua cac tu ghep lay top_k
        top_indices = sorted(range(len(doc_scores)), key = lambda i:doc_scores[i], reverse=True)[:top_k]
        results = []
        for i in top_indices:
            results.append({
                "doc_id": self.documents[i]["doc_id"],
                "content": self.documents[i]["content"],
                "source": self.documents[i]["source"],
                "score": float(doc_scores[i])
            })
        return results 
        