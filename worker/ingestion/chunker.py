import re
import json

def chunk_regulatory_handbook(text_content, filename):
    """
    Hàm này dùng để chunk các đoạn văn. Kiểu chunk ở đây theo cấu trúc 
    Chương, Điều,... dùng regex để chunk.
    """

def chunk_academic_calendar(text_content, filename):
    """
    Hàm này dùng để chunk các đoạn văn. Kiểu chunk ở đây theo cấu trúc 
    Chương, Điều,... dùng regex để chunk.
    """







def chunk_raw_web1(json_string, filename):
    """
    Hàm chunk nội dung từ file json raw_web.
    Đọc json_string để lấy url, title và content, 
    sau đó chunk content theo từng dòng với độ dài tối đa.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        return []

    url = data.get("url", "")
    title = data.get("title", "")
    content = data.get("content", "")

    if not content:
        return []

    # Tách theo dòng để đảm bảo không cắt ngang giữa câu nếu không cần thiết
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    
    chunks = []
    current_chunk = ""
    MAX_LENGTH = 1000 # Kích thước tối đa cho mỗi chunk

    for p in paragraphs:
        if len(current_chunk) + len(p) + 1 <= MAX_LENGTH:
            current_chunk = current_chunk + "\n" + p if current_chunk else p
        else:
            if current_chunk:
                chunks.append({
                    "text": current_chunk,
                    "metadata": {"source": filename, "url": url, "title": title}
                })
            
            # Xử lý trường hợp một dòng quá dài (> MAX_LENGTH)
            if len(p) > MAX_LENGTH:
                while len(p) > MAX_LENGTH:
                    chunks.append({
                        "text": p[:MAX_LENGTH],
                        "metadata": {"source": filename, "url": url, "title": title}
                    })
                    p = p[MAX_LENGTH:]
                current_chunk = p
            else:
                current_chunk = p

    if current_chunk:
        chunks.append({
            "text": current_chunk,
            "metadata": {"source": filename, "url": url, "title": title}
        })

    return chunks






def master_chunk(text_content, filename, folder_type):
    """Hàm này quyết định xem nên dùng kiểu chunk nào phụ thuộc vào folder"""
    if folder_type == "raw_web":
        return chunk_raw_web1(text_content, filename)
    else:
        if "KẾ HOẠCH HỌC TẬP" in text_content:
            return chunk_academic_calendar(text_content, filename)
        else:
            return chunk_regulatory_handbook(text_content, filename)



