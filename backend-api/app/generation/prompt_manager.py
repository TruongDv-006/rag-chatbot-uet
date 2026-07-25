import urllib.parse

# Class chuyên trách đóng gói và quản lý Prompt Template

class PromptManager:
    """
    Class này đảm nhận nhiệm vụ quản lý và thiết kế cấu trúc câu lệnh Prompt
    """
    
    def __init__(self):
        self._system_template = (
            "Bạn là trợ lý tư vấn học vụ UET (Trường Đại học Công nghệ - ĐHQGHN).\n"
            "Nhiệm vụ của bạn là trả lời câu hỏi một cách tự nhiên, lịch sự, đúng trọng tâm và CHỈ dựa trên Ngữ cảnh được cung cấp.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. Cứ mỗi thông tin bạn đưa ra trong bài, bạn PHẢI chèn ngay ký hiệu [Tài liệu X] tương ứng phía sau thông tin đó.\n"
            "   Ví dụ: Phòng CTSV có địa chỉ tại Phòng 104-E3 [Tài liệu 1]. SĐT liên hệ là 02437548864 [Tài liệu 2].\n"
            "2. Không viết gộp dạng '[Tài liệu 1 - Tài liệu 2]'. Mỗi tài liệu trích dẫn phải viết riêng rẽ như: [Tài liệu 1] [Tài liệu 2].\n"
            "3. Tuyệt đối không tự suy diễn hoặc sử dụng kiến thức bên ngoài Ngữ cảnh.\n\n"
            "NẾU KHÔNG CÓ THÔNG TIN TRONG NGỮ CẢNH:\n"
            "Trả lời đúng duy nhất câu: \"Tôi không có đủ dữ liệu để trả lời câu hỏi này. Bạn vui lòng tham khảo Sổ tay sinh viên hoặc liên hệ Phòng Đào tạo UET để được hỗ trợ.\""
        )

    def create_messages(self, retrieved_docs: list[dict], query: str):
        """
        Đóng gói ngữ cảnh(context) và Query thành 1 định dạng chuẩn
        """
        context_parts = []
        for i, doc in enumerate(retrieved_docs, start=1):
            text_content = doc.get("content", "")
            raw_source = doc.get("source", f"Tài liệu {i}")
            clean_source = urllib.parse.unquote(raw_source)
            if clean_source.endswith("_parsed.txt"):
                clean_source = clean_source[:-11]
            context_parts.append(f"[Tài liệu {i}] (Nguồn: {clean_source}): {text_content}")

        formatted_context = "\n\n".join(context_parts) if context_parts else "Không có tài liệu."
        full_system_prompt = f"{self._system_template}\n\nNgữ cảnh:\n{formatted_context}"

        return [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": query}
        ]