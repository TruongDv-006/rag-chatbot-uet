import urllib.parse

# Class chuyên trách đóng gói và quản lý Prompt Template

class PromptManager:
    """
    Class này đảm nhận nhiệm vụ quản lý và thiết kế cấu trúc câu lệnh Prompt
    """
    
    def __init__(self):
        self._system_template = (
            "Bạn là trợ lý tư vấn học vụ UET. Trả lời trực diện, đúng sự thật, 100% bằng Tiếng Việt KHÔNG được dùng ngôn ngữ khác và CHỈ dựa vào Ngữ cảnh được cung cấp.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. CHỈ trả lời ĐÚNG CHỦ THỂ người dùng đang hỏi. Tuyệt đối KHÔNG liệt kê thêm thông tin của các đơn vị khác không được hỏi.\n"
            "2. CHỈ đưa ra thông tin CÓ THỰC TRONG NGỮ CẢNH. Tuyệt đối KHÔNG tự bịa đặt, KHÔNG tự suy diễn thêm và KHÔNG tự quy đổi thang điểm (như quy đổi C+ ra B hoặc thang điểm 10/100) nếu ngữ cảnh không ghi rõ.\n"
            "3. BẮT BUỘC PHÂN BIỆT RÕ RÀNG THUẬT NGỮ HỌC VỤ (Ưu tiên Quy chế hiện hành mới nhất Quy-chế-ĐTHĐ-3626):\n"
            "   - 'HỌC LẠI': CHỈ áp dụng duy nhất đối với học phần BỊ ĐIỂM F (học phần không đạt/bị trượt).\n"
            "   - 'HỌC CẢI THIỆN ĐIỂM': Áp dụng đối với học phần ĐẠT ĐIỂM D, D+ (học phần đã đạt, sinh viên đăng ký để nâng cao điểm trung bình tích lũy). TUYỆT ĐỐI KHÔNG dùng thuật ngữ 'học lại' khi nói về điểm D, D+. Nếu người dùng hỏi hoặc nhắc nhở điểm D chỉ được học cải thiện chứ không được học lại, hãy đồng ý và khẳng định chính xác: Điểm D/D+ là học phần đã đạt nên hình thức đăng ký là 'Học cải thiện điểm'.\n"
            "   - 'ĐIỂM C TRỞ LÊN' (gồm C, C+, B, B+, A, A+): TUYỆT ĐỐI KHÔNG ĐƯỢC đăng ký học lại và KHÔNG ĐƯỢC đăng ký học cải thiện điểm dưới bất kỳ hình thức nào (dù là bắt buộc hay tự chọn).\n"
            "4. Cứ mỗi thông tin trả lời, PHẢI chèn ký hiệu [Tài liệu X] tương ứng phía sau (ví dụ: [Tài liệu 1]). Không viết gộp dạng '[Tài liệu 1 - Tài liệu 2]'. Không tự tạo danh sách 'Nguồn tham khảo' hay chèn link ở cuối bài.\n"
            "5. Nếu là câu chào hỏi xã giao: Trả lời ngắn gọn, KHÔNG chèn [Tài liệu X].\n"
            "6. Nếu Ngữ cảnh KHÔNG chứa thông tin trực tiếp trả lời cho chủ thể được hỏi, CHỈ trả lời đúng duy nhất câu: \"Tôi không có đủ dữ liệu để trả lời câu hỏi này. Bạn vui lòng tham khảo Sổ tay sinh viên hoặc liên hệ Phòng Đào tạo UET để được hỗ trợ.\""
        )

    def create_query_rewrite_messages(self, query: str, chat_history: list[dict] | None = None):
        """
        Tạo prompt để viết lại câu hỏi mới dựa trên 1 tin nhắn gần nhất trong lịch sử hội thoại,
        biến câu hỏi thành một câu hỏi độc lập (Standalone Query) đầy đủ ý nghĩa trước khi tìm kiếm RAG.
        """
        history_str = ""
        if chat_history:
            formatted = []
            for msg in chat_history:
                role_label = "Sinh viên" if msg.get("role") == "student" else "Trợ lý AI"
                formatted.append(f"{role_label}: {msg.get('content', '')}")
            history_str = "\n".join(formatted)

        system_prompt = (
            "Bạn là trợ lý xử lý ngôn ngữ tự nhiên. Nhiệm vụ của bạn là xem xét Lịch sử hội thoại "
            "và Câu hỏi mới của sinh viên để chuyển câu hỏi mới thành MỘT CÂU HỎI ĐỘC LẬP (Standalone Query).\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. CHỈ xuất duy nhất câu hỏi đã viết lại. KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG dùng ngôn ngữ khác.\n"
            "2. CHỈ bổ sung chủ thể từ Lịch sử hội thoại NẾU câu hỏi mới sử dụng đại từ thay thế (ví dụ: 'nó', 'đó', 'môn đó', 'cái này', 'ở đâu', 'bao nhiêu') hoặc là câu hỏi nối tiếp khuyết chủ ngữ.\n"
            "3. Khi giải nghĩa từ tham chiếu ('môn đó', 'nó', 'cái đó'), BẮT BUỘC thay thế bằng tên chủ thể cụ thể từ lịch sử (ví dụ: 'môn đó' thì 'học phần đạt điểm C+').\n"
            "4. NẾU câu hỏi mới đã đầy đủ chủ ngữ/vị ngữ hoặc chuyển sang một chủ đề hoàn toàn mới, GIỮ NGUYÊN CÂU HỎI MỚI, TUYỆT ĐỐI KHÔNG ghép thêm tên đơn vị, địa điểm hoặc chủ thể từ câu hỏi trước."
        )

        user_content = f"Lịch sử hội thoại gần đây:\n{history_str}\n\nCâu hỏi mới: {query}\n\nCâu hỏi độc lập:"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

    def create_messages(self, retrieved_docs: list[dict], query: str, chat_history: list[dict] | None = None):
        """
        Đóng gói ngữ cảnh (context) và Query thành 1 định dạng chuẩn.
        Tự động gộp các đoạn văn (chunks) thuộc cùng 1 file tài liệu thành 1 [Tài liệu X] duy nhất.
        """
        # Gộp các chunks theo tên file nguồn (dict[tên_file, danh_sách_đoạn_văn])
        grouped_docs: dict[str, list[str]] = {}
        for doc in retrieved_docs:
            raw_source = doc.get("source")
            if not raw_source or not str(raw_source).strip():
                clean_source = "Sổ tay sinh viên UET"
            else:
                clean_source = urllib.parse.unquote(str(raw_source)).strip()
                if clean_source.endswith("_parsed.txt"):
                    clean_source = clean_source[:-11]
            
            content = doc.get("content", "").strip()
            if not content:
                continue

            if clean_source not in grouped_docs:
                grouped_docs[clean_source] = []
            
            if content not in grouped_docs[clean_source]:
                grouped_docs[clean_source].append(content)

        sorted_items = sorted(
            grouped_docs.items(),
            key=lambda item: 0 if "3626" in item[0] else (1 if "2014" in item[0] else 2)
        )

        context_parts = []
        for i, (src_name, contents) in enumerate(sorted_items, start=1):
            merged_text = "\n---\n".join(contents)
            context_parts.append(f"[Tài liệu {i}] (Nguồn: {src_name}):\n{merged_text}")

        formatted_context = "\n\n".join(context_parts) if context_parts else "Không có tài liệu."
        full_system_prompt = f"{self._system_template}\n\nNgữ cảnh:\n{formatted_context}"

        messages = [
            {"role": "system", "content": full_system_prompt}
        ]
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.get("role") == "student" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": query})        
        return messages