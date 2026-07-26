import re
import json

def chunk_regulatory_handbook(text_content, filename):
    """
    Hàm này dùng để chunk các đoạn văn. Kiểu chunk ở đây theo cấu trúc 
    Chương, Điều,... dùng regex để chunk.
    """
    chunks = []
    current_chuong = "Thong tin chung"
    current_dieu = "Thong tin chung"
    current_contents = []

    lines = text_content.split("\n")
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if re.match(r'^Chương\s+[IVXLCDM\d]+', line, re.IGNORECASE):
            if current_contents:
                chunks.append({
                    "text": "\n".join(current_contents),
                    "metadata" : {"source":filename, "chuong": current_chuong, "dieu": current_dieu, "type":"quy_che"} 
                })
            current_chuong = line
            current_dieu = "Mo dau chuong"
            current_contents = [line]
        elif re.match(r'^Điều\s+\d+', line, re.IGNORECASE):
            if current_contents:
                chunks.append({
                    "text": "\n".join(current_contents),
                    "metadata" : {"source":filename, "chuong":current_chuong, "dieu":current_dieu, "type":"quy_che"}
                })
            current_contents = [line]
            current_dieu = line
        else: 
            current_contents.append(line)
        
    if current_contents:
            chunks.append({
                "text": "\n".join(current_contents),
                "metadata" : {"source":filename, "chuong":current_chuong, "dieu":current_dieu, "type":"quy_che"}
            })
            current_contents = [line]
    return chunks

def chunk_academic_calendar(text_content, filename):
    """
    Hàm này dùng để chunk các đoạn văn. Kiểu chunk ở đây theo cấu trúc 
    Chương, Điều,... dùng regex để chunk.
    """
    chunks = []
    current_hocky = "Thong tin chung"
    current_chunk_lines = []
    MAX_LENGTH = 800

    lines = text_content.split("\n")
    for line in lines:
        line = line.strip()
        if not line : continue
        
        if re.match(r'^HỌC KỲ\s+[I|II|PHỤ]',line, re.IGNORECASE):
            if current_chunk_lines:
                text_to_save = f"Giai đoạn: {current_hocky}\nNội dung lịch trình:\n" + "\n".join(current_chunk_lines)
                chunks.append({
                    "text" : text_to_save,
                    "metadata" : {"source": filename, "chuong": "Ke hoach hoc tap", "dieu": current_hocky, "type" : "lich trinh"}
                })
                current_chunk_lines = []
            current_hocky = line
            continue
        header_len = len(f"Giai đoạn: {current_hocky}\nNội dung lịch trình:\n")
        current_len = sum(len(l)+1 for l in current_chunk_lines)
        if header_len + current_len + len(line) + 1 > MAX_LENGTH:
            text_to_save = f"Giai đoạn: {current_hocky}\nNội dung lịch trình:\n" + "\n".join(current_chunk_lines)
            chunks.append({
                "text" : text_to_save,
                "metadata" : {"source": filename, "chuong": "Ke hoach hoc tap", "dieu": current_hocky, "type" : "lich trinh"}
            })
            current_chunk_lines = [line]
        else:
            current_chunk_lines.append(line)
    if current_chunk_lines:
        text_to_save = f"Giai đoạn: {current_hocky}\nNội dung lịch trình:\n" + "\n".join(current_chunk_lines)
        chunks.append({
            "text" : text_to_save,
            "metadata" : {"source": filename, "chuong": "Ke hoach hoc tap", "dieu": current_hocky, "type" : "lich trinh"}
        }) 
    return chunks


def chunk_raw_web(json_string, filename):
    """
    Hàm chunk tối ưu cho raw_web:
    - Chèn tiêu đề trang (Title) vào đầu mỗi chunk để giữ ngữ cảnh.
    - Gộp 3 - 5 dòng liên tiếp (khoảng 300 - 400 ký tự) có độ gối đầu (overlap)
      để đảm bảo thông tin liên hệ/thủ tục không bị ngắt rời rạc.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError:
        return []

    url = data.get("url", "")
    title = data.get("title", "")
    content = data.get("content", "")

    if not content or not content.strip():
        return []

    lines = [line.strip() for line in content.split('\n') if line.strip()]
    if not lines:
        return []

    chunks = []
    MAX_CHUNK_SIZE = 350  # Kích thước tối ưu cho 1 khối thông tin web
    OVERLAP_LINES = 1     # Gối đầu 1 dòng giữa các chunk

    i = 0
    while i < len(lines):
        current_lines = []
        current_len = 0
        
        j = i
        while j < len(lines):
            line = lines[j]
            if current_len + len(line) > MAX_CHUNK_SIZE and current_lines:
                break
            current_lines.append(line)
            current_len += len(line)
            j += 1

        chunk_text = f"Trang: {title}\n" + "\n".join(current_lines)
        chunks.append({
            "text": chunk_text,
            "metadata": {"source": filename, "url": url, "title": title}
        })

        advance = max(1, len(current_lines) - OVERLAP_LINES)
        i += advance

    return chunks


def master_chunk(text_content, filename, folder_type):
    """Hàm này quyết định xem nên dùng kiểu chunk nào phụ thuộc vào folder"""
    if folder_type == "raw_web":
        return chunk_raw_web(text_content, filename)
    else:
        if "KẾ HOẠCH HỌC TẬP" in text_content:
            return chunk_academic_calendar(text_content, filename)
        else:
            return chunk_regulatory_handbook(text_content, filename)



