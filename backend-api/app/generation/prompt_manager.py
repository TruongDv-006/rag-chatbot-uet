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
            "QUY TẮC TRÍCH DẪN NỘI VĂN (IN-TEXT CITATION):\n"
            "1. Trong phần ngữ cảnh, các đoạn văn bản đã được đánh số thứ tự dạng [Tài liệu 1], [Tài liệu 2],...\n"
            "2. Khi viết câu trả lời, cứ sau mỗi câu văn sử dụng thông tin từ tài liệu nào, bạn PHẢI chèn ký hiệu của tài liệu đó ngay phía sau câu văn (ví dụ: Bạn cần duy trì GPA từ 3.6 trở lên [Tài liệu 1]. Hoàn thành đóng học phí đúng hạn [Tài liệu 2]).\n"
            "3. Nếu một câu văn tổng hợp thông tin từ nhiều nguồn, bạn có thể chèn nhiều ký hiệu liền nhau (ví dụ: Quy chế áp dụng cho cả sinh viên hệ chuẩn và CLC [Tài liệu 1][Tài liệu 3]).\n\n"
            "QUY TẮC BẮT BUỘC (ANTI-HALLUCINATION):\n"
            "1. Tuyệt đối không sử dụng kiến thức bên ngoài hoặc tự suy diễn, đoán mò.\n"
            "2. Nếu ngữ cảnh được cung cấp KHÔNG CHỨA thông tin phù hợp để trả lời câu hỏi, "
            "bạn PHẢI trả lời chính xác câu sau, không thêm bớt từ: "
            "\"Tôi không có đủ dữ liệu để trả lời câu hỏi này. Bạn vui lòng tham khảo Sổ tay sinh viên hoặc liên hệ Phòng Đào tạo UET để được hỗ trợ.\"\n"
            "3. Không bịa đặt thông tin và không tự tạo ra các ký hiệu tài liệu không tồn tại trong ngữ cảnh được cung cấp."
        )

    def create_messages(self, retrieved_docs: list[dict], query: str):
        """
        Đóng gói ngữ cảnh(context) và Query thành 1 định dạng chuẩn
        - retrieved_docs: Danh sách các dict tài liệu đã qua lọc điểm threshold
        - query: Câu hỏi user gõ trên khung chat giao diện
        """
        context_parts = []
        for i, doc in enumerate(retrieved_docs, start=1):
            text_content = doc.get("content", "")
            context_parts.append(f"[Tài liệu {i}: {text_content}]")

            formatted_context = "\n\n".join(context_parts)
            full_system_prompt = f"{self._system_template}\n\nNgữ cảnh(context):\n{formatted_context}"

        return [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": query}
        ]