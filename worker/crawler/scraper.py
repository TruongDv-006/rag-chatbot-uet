import os
import time
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Đường dẫn cần save sau khi scraping xong
SAVE_DIR = "../../infrastructure/volumes/minio_data/raw_web"
DOCS_DIR = "../../infrastructure/volumes/minio_data/documents"

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(DOCS_DIR,exist_ok=True)

class UetHandbookScraper:
    def __init__ (self, base_url):
        self.base_url = base_url # Lấy đường dẫn

        self.domain = urlparse(base_url).netloc # Lấy tên miền gốc
        
        self.urls_visit = [base_url] # Tạo danh sách các url cần thăm
        
        self.visited_url = set() # Các url đã thăm (set có độ phức tạp tìm kiếm O(1))

        self.session = requests.Session() # Tạo ra 1 phiên session giữ cửa

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:149.0) Gecko/20100101 Firefox/149.0"
        }) 
    
    def is_valid_url(self, url):
        """ Ham nay kiem tra xem url nay co phai la 1 url can tham khong
        """
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        if netloc == self.domain:
            if url.lower().endswith(('.jpg', '.png', '.zip', '.rar', '.mp4')):
                return False
            return True

        if "vnu.edu.vn" in netloc:
            if url.lower().endswith(('.pdf', '.docx', '.doc')) or any(keyword in url.lower() for keyword in ['/upload/', '/vanban/', '/data/']):
                return True
        return False
    def extract_content(self, soup):
        """ Hàm này dùng để trích xuất những nội dung cần dùng
            Đồng thời loại bỏ những thẻ thừa, nội dung không cần thiết
        """
        
        #Func decompose dung de pha huy
        for tag in soup.find_all(["head","script","style", "footer"]):
            tag.decompose()
        for tag in soup.find_all("div", class_ = "nav-bar"):
            tag.decompose()

        footer_keywords = {
            "Biên tập: Phòng CTSV",
            "Thiết kế: SV Trường ĐHCN",
            "Thiết kế: SV trường ĐHCN",
            "Email: ctsv_dhcn@vnu.edu.vn",
            "Phòng 104-E3, 144 Xuân Thủy, Cầu Giấy, Hà Nội",
            "ĐT: 02437548864"
        }

        content_blocks = []
        # Lay noi dung tu khoi main-content tro di
        body_content = soup.find("body")
        if body_content:
            for tag in body_content.find_all(['span', 'p', 'h1', 'h2', 'h3','li','td','th']):
                if tag.find(['span', 'p', 'h1', 'h2', 'h3', 'li', 'td', 'th']):
                    continue
                text = tag.get_text(strip=True)
                if text and text not in footer_keywords and text not in content_blocks:
                    content_blocks.append(text)
        return "\n".join(content_blocks)

    def crawl(self, limit=50):
        """ 
        Hàm cào dữ liệu với limit=50 cho 1 lần cào
        """
        count = 0
        while self.urls_visit and count < limit:
            current_url = self.urls_visit.pop(0)
            #Nếu đã được thăm rồi thì bỏ qua 
            if current_url in self.visited_url:
                continue
            try:
                response = self.session.get(current_url, timeout=10)
                if response.status_code == 200:
                    """Xử lý các file .pdf .docx và .docx
                    """ 
                    if current_url.lower().endswith(('.pdf','.doc','docx')):
                        file_name = current_url.split('/')[-1]
                        file_path = os.path.join(DOCS_DIR, file_name)

                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Đã tải thành công file đính kèm: {file_name}")
                        self.visited_url.add(current_url)
                        count+=1
                        continue

                    """Xử lý tiếp nếu không phải các file tĩnh
                    """
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text,'html.parser')

                    # Đảm bảo cả soup.title và soup.title.string đều tồn tại thì mới lấy, không thì lấy "no-title"
                    title = soup.title.string if (soup.title and soup.title.string) else "no-title"
                    text_content = self.extract_content(soup)
                    if text_content.strip():
                        # Làm sạch tên tiêu đề (xóa ký tự lạ) để đặt tên file không bị lỗi hệ điều hành
                        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-')]).strip()
                        file_name = f"{safe_title}.json"
                        file_path = os.path.join(SAVE_DIR, file_name)
                        # Dong goi du lieu
                        data = {
                            "url" : current_url,
                            "title": title,
                            "content": text_content
                        }
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        count += 1
                    
                    # Danh dau da tham 
                    self.visited_url.add(current_url)
                    # Lấy các đường dẫn từ trang hiện tại ra cào tiếp
                    for link in soup.find_all('a', href=True):
                        full_link = urljoin(current_url, link['href']).split('#')[0]
                        if self.is_valid_url(full_link) and full_link not in self.visited_url and full_link not in self.urls_visit:
                                self.urls_visit.append(full_link)
                time.sleep(1)
            except Exception as e:
                print(f"Loi khi dang cao {current_url}:{e}")


if __name__ == "__main__":
    target_url = "https://handbook.uet.vnu.edu.vn"

    crawler = UetHandbookScraper(target_url) 
    crawler.crawl()




    