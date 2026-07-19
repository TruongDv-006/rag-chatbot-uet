class RankFusion:
    def __init__(self, k:int=60):
        """
        Khởi tạo bộ trộn thứ hạng RRF(Reciprocal Rank Fusion)    
        Hằng số làm mượt : k=60(tùy chỉnh)
        """
        self.k=k

    def reciprocal_rank_fusion(self, semantic_results: list[dict], keyword_results: list[dict]):
        """
        Hàm trộn này dùng để tính điểm và xếp hạng lại kết quả từ 2 luồng tìm kiếm bằng thuật toán RRF
        Trong đó:
        - semantic_results: Kết quả từ Semantic Search
                            Dạng: [{"doc_id":"...", "content":"...", "source":"...", "score":"..."}]
        - keyword_results: Kết quả trả về từ Keyword Search
                            Dạng: [{"doc_id":"...", "content":"...", "source":"...", "score":"..."}]
        """
        #dict nay dung de luu ket qua sau khi hop nhat va co dang "doc_id": rrf_score
        rrf_scores : dict[str, float] = {}
        #dict nay dung de luu ket qua sau khi hop nhat va co dang "doc_id": content
        fused_docs: dict[str, str]={}
        # dict nay dung de luu source sau khi hop nhat va co dang "doc_id": source
        fused_source: dict[str, str]={}

        def add_to_rrf(results: list[dict]):
            nonlocal rrf_scores, fused_docs
            for rank, doc in enumerate(results):
                doc_id = str(doc["doc_id"])
                content = str(doc["content"])
                doc_source = str(doc["source"])
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id]=0.0
                    fused_docs[doc_id]=content
                    fused_source[doc_id]=doc_source
                rrf_scores[doc_id] += 1.0 / (self.k + rank + 1)
            
        add_to_rrf(semantic_results)

        add_to_rrf(keyword_results)

        sorted_fused = sorted(rrf_scores.items(), key=lambda x:x[1], reverse=True)

        final_results = []
        for doc_id, score in sorted_fused:
            final_results.append({
                "doc_id" : doc_id,
                "content": fused_docs[doc_id],
                "source": fused_source[doc_id],
                "score" : score
            })
        return final_results