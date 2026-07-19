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
        return chunk_raw_web(text_content, filename)
    else:
        if "KẾ HOẠCH HỌC TẬP" in text_content:
            return chunk_academic_calendar(text_content, filename)
        else:
            return chunk_regulatory_handbook(text_content, filename)



