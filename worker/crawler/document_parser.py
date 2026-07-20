import pdfplumber
import os
import docx
import pytesseract
from pdf2image import convert_from_path
import re

# Đường dẫn này chứa các file PDF, DOCX tải về
SOURCE_DOCS_DIR = "../../infrastructure/volumes/minio_data/documents"
# Đường dẫn này chứa các file PDF, DOCX sau khi đã làm sạch
PARSER_DOCS_DIR = "../../infrastructure/volumes/minio_data/docs_parsed"

os.makedirs(SOURCE_DOCS_DIR, exist_ok=True)
os.makedirs(PARSER_DOCS_DIR, exist_ok=True)



class DocumentParser:
    @staticmethod
    def clean_pdf_text(raw_text):
        # 1. Xóa số trang
        cleaned = re.sub(r'^\s*\d+\s*$\n?', '', raw_text, flags=re.MULTILINE)
        
        # 2. Nối các câu bị đứt đoạn do xuống dòng vật lý
        cleaned = re.sub(r'(?<![.:!?;\-])\n+', ' ', cleaned)
        
        # 3. MỚI THÊM: Tách các mục lục (Điều X., 1., a)) bị dính chùm xuống dòng mới
        # Cú pháp này tìm các khoảng trắng nằm ngay trước các từ khóa danh sách và biến nó thành \n
        cleaned = re.sub(
        r'(?<=[^\s])(?<!Điều)(?<!ĐIỀU)(?<!Chương)(?<!CHƯƠNG)\s+(?=(Điều\s+\d+|[1-9]+\.|[a-zđĐ]\)))', 
        '\n', 
        cleaned,
        flags=re.IGNORECASE
        )
        
        # 4. Dọn dẹp khoảng trắng thừa
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        return cleaned.strip()
    @staticmethod
    def parse_pdf(self,file_path):
        """Trích xuất chữ từ file PDF
        """
        text_content = ""
        try:
            # SỬ DỤNG PDFPLUMBER THAY VÌ PYPDF2
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted.strip():
                        text_content += extracted + "\n"
            #Nếu là file pdf scan chuỗi sẽ về rỗng vì vậy dùng OCR tại đây
            if not text_content.strip():
                images = convert_from_path(file_path)
                
                for i, image in enumerate(images):
                    # Sử dụng Tesseract để đọc chữ từ tấm ảnh (cấu hình ngôn ngữ 'vie' = Tiếng Việt)
                    ocr_text = str(pytesseract.image_to_string(image, lang='vie') or "")
                    if ocr_text:
                        text_content = text_content + ocr_text + "\n"

            final_text = self.clean_pdf_text(text_content)
            
            return final_text
        except Exception as e:
            print(f"Lỗi khi đọc file PDF {file_path}:{e}")
            return ""

    @staticmethod
    def parse_docx(file_path):
        """Trích xuất chữ thì file docx
        """
        text_content = ""
        try:
            with open(file_path, 'rb') as file:
                doc = docx.Document(file)

                for para in doc.paragraphs:
                    if para.text.strip():
                        text_content += para.text + "\n"

            return text_content
        except Exception as e:
            print(f"Lỗi khi đọc file DOCX {file_path}:{e}")
            return ""
        
    def process_directory(self):
        """Quét toàn bộ thư mục và xử lý các file PDF, DOCX
        """
        files = os.listdir(SOURCE_DOCS_DIR)

        for filename in files:
            file_path = os.path.join(SOURCE_DOCS_DIR, filename)
            content = ""

            if(filename.lower().endswith('.pdf')):
                content = self.parse_pdf(self, file_path)
            elif (filename.lower().endswith('.docx')):
                content = self.parse_docx(file_path)
            else:
                print(f"Không hỗ trợ định dạng này: {filename}")

            if content.strip():
                base_name = os.path.splitext(filename)[0]
                save_path = os.path.join(PARSER_DOCS_DIR,f"{base_name}_parsed.txt")
                with open(save_path, 'w', encoding = 'utf-8') as f:
                    f.write(content)
if __name__ == "__main__":
    parser = DocumentParser()

    parser.process_directory()



