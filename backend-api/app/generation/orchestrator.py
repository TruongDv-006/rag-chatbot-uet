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
        Hàm thực thi chính của luồng RAG
        """
        threshold = score_threshold or generation_config.DEFAULT_SCORE_THRESHOLD

        valid_docs = [doc for doc in retrieved_docs if doc.get("score",0.0) >= threshold]

        #Nếu danh sách trả về rỗng chứng tỏ không có tài liệu nào đạt ngưỡng 
        if not valid_docs:
            print(f"[Hệ thống chặn ngầm] Câu hỏi '{query}' bị từ chối vì không có tài liệu nào đạt chuẩn.")
            return self.fallback_message

        # context_text = "\n\n".join([doc["text"] for doc in valid_docs])

        messages = self.prompt_manager.create_messages(valid_docs, query)

        try:
            answer = self.llm_client.generate(messages)
            return answer
        except Exception as e:
            print("Lỗi hệ thống: {e}")
            return "Hệ thống đang gặp sự cố kết nối với mô hình ngôn ngữ. Vui lòng thử lại sau."