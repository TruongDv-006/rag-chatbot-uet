# Class trung tâm điều phối RAG và lọc Anti-Hallucination
from app.generation.config import generation_config # pyrefly: ignore [missing-import]
from app.generation.prompt_manager import PromptManager # pyrefly: ignore [missing-import]
from app.generation.llm_client import LLMClient # pyrefly: ignore [missing-import]

class RAGGenerator:

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

        self.prompt_manager = PromptManager()

        self.fallback_message = (
            "Tôi không có đủ dữ liệu để trả lời câu hỏi này. "
            "Bạn vui lòng tham khảo Sổ tay sinh viên hoặc liên hệ Phòng Đào tạo UET để được hỗ trợ."
        )



    #Nếu cần mở rộng thì sẽ cần hàm này tuy nhiên với hệ thống RAG cơ bản như hiện tại thì không cần
    # def _validate_retrieval_quality(self, retrieved_docs:list[dict], threshold:float):
    #     """
    #     Hàm này kiểm tra xem có tài liệu nào lấy từ Vector DB có đoạn nào đủ tin cậy không
    #     Điều này chống Anti-Hallucination
    #     """
    


    def execute(self, query:str, retrieved_docs:list[dict], score_threshold: float):
        """
        Hàm thực thi chính của luồng RAG.
        - score_threshold = 0.0  → Chưa có embedding (Qdrant trống), vẫn gọi LLM
        - score_threshold > 0.0  → Lọc tài liệu, chặn hallucination nếu không đủ điểm
        """
        threshold = score_threshold  # Caller đã tính toán ngưỡng phù hợp

        # Lọc tài liệu chỉ khi có ngưỡng hợp lệ
        if threshold > 0.0:
            valid_docs = [doc for doc in retrieved_docs if doc.get("score", 0.0) >= threshold]
            # Không có tài liệu đạt chuẩn → fallback, chống hallucination
            if not valid_docs:
                print(f"[Anti-Hallucination] Câu hỏi '{query}' bị từ chối vì không có tài liệu đạt chuẩn (ngưỡng={threshold}).")
                return self.fallback_message
        else:
            # threshold=0.0: Qdrant chưa có dữ liệu → LLM trả lời dựa trên kiến thức chung
            valid_docs = retrieved_docs or []
            print(f"[RAG] Không có embedding, LLM sẽ trả lời dựa trên kiến thức chung cho: '{query}'")

        messages = self.prompt_manager.create_messages(valid_docs, query)

        try:
            answer = self.llm_client.generate(messages)
            return answer
        except Exception as e:
            print(f"Lỗi hệ thống: {e}")
            return "Hệ thống đang gặp sự cố kết nối với mô hình ngôn ngữ. Vui lòng thử lại sau."