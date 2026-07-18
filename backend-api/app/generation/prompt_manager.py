# Class chuyên trách đóng gói và quản lý Prompt Template

class PromptManager:
    """
    Class này đảm nhận nhiệm vụ quản lý và thiết kế cấu trúc câu lệnh Prompt
    """
    
    def __init__(self):
        self._system_template = (
            "Bạn là trợ lý ảo hỗ trợ học vụ cho sinh viên trường Đại học Công nghệ, "
            "Đại học Quốc gia Hà Nội (UET - VNU).\n"
            "Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên một cách ngắn gọn, chính xác "
            "và CHỈ DỰA TRÊN NGỮ CẢNH (Context) được cung cấp dưới đây.\n\n"
            "QUY TẮC BẮT BUỘC (ANTI-HALLUCINATION):\n"
            "1. Tuyệt đối không sử dụng kiến thức bên ngoài hoặc tự suy diễn, đoán mò.\n"
            "2. Nếu ngữ cảnh được cung cấp KHÔNG CHỨA thông tin phù hợp để trả lời câu hỏi, "
            "bạn PHẢI trả lời chính xác câu sau, không thêm bớt từ: "
            "\"Tôi không có đủ dữ liệu để trả lời câu hỏi này. Bạn vui lòng tham khảo Sổ tay sinh viên hoặc liên hệ Phòng Đào tạo UET để được hỗ trợ.\"\n"
            "3. Không bịa đặt thông tin."
        )

        def create_messages(self, context:str, query:str):
            """
            Đóng gói ngữ cảnh(context) và Query thành 1 định dạng chuẩn
            - context: Đoạn văn bản Sổ tay UET tìm được từ Vector DB
            - query: Câu hỏi user gõ trên khung chat giao diện
            """
            full_system_prompt = f"{self._system_template}\n\nNgữ cảnh(context):\n{context}"

            return [
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": query}
            ]