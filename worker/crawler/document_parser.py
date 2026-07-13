import PyPDF2
import os
import docx


# Đường dẫn này chứa các file PDF, DOCX tải về
SOURCE_DOCS_DIR = "../../infrastructure/volumes/minio_data/documents"
# Đường dẫn này chứa các file PDF, DOCX sau khi đã làm sạch
PARSER_DOCS_DIR = "../../infrastructure/volumes/minio_data/docs_parsed"

os.makedirs(SOURCE_DOCS_DIR, exist_ok=True)
os.makedirs(PARSER_DOCS_DIR, exist_ok=True)



class DocumentParser:
    @staticmethod
    def parse_pdf(file_path):
        """Trích xuất chữ từ file PDF
        """
        text_content = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)

                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    extracted = page.extract_text()
                    if extracted:
                        text_content += extracted + "\n"

            return text_content
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
                content = self.parse_pdf(file_path)
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



