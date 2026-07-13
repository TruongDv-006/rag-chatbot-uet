import os
import time
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Đường dẫn cần save sau khi scraping xong
SAVE_DIR = "../../infrastructure/volumes/minio_data/raw_web"

os.makedirs(SAVE_DIR, exist_ok=True)


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
            Có 2 trường hợp cần phải loại bỏ:
                1. Nếu tên domain không trùng với tên domain của miền gốc
                2. Các đường link dẫn tới file tài liệu tĩnh
        """
        parsed = urlparse(url)
        if parsed.netloc != self.domain:
            return False
        
        if url.lower().endswith(('.pdf', '.doc', '.docx', '.jpg', '.png', '.zip')):
            return False

        return True

    def extract_content(self, soup):
        """ Hàm này dùng để trích xuất những nội dung cần dùng
            Đồng thời loại bỏ những thẻ thừa, nội dung không cần thiết
        """
        
        #Func decompose dung de pha huy
        for tag in soup.find_all(["head","script","style", "footer"]):
            tag.decompose()
        for tag in soup.find_all("div", class_ = "nav-bar"):
            tag.decompose()

        content_blocks = []
        # Lay noi dung tu khoi main-content tro di
        body_content = soup.find("body")
        if body_content:
            for tag in body_content.find_all(['span', 'p', 'h1', 'h2', 'h3','li','td','th']):
                text = tag.get_text(strip=True)
                if text:
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
                # Gửi yêu cầu tới trang web quá 10s thì ngắt bỏ
                response = self.session.get(current_url, timeout=10)
                response.encoding = 'utf-8'
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text,'html.parser')

                    title = soup.title.string if soup.title else "no-title"
                    text_content = self.extract_content(soup)
                    if text_content.strip():
                        # Làm sạch tên tiêu đề (xóa ký tự lạ) để đặt tên file không bị lỗi hệ điều hành
                        safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-')]).strip()
                        file_name = f"{safe_title}.json"
                        file_path = os.path.join(SAVE_DIR, file_name)
                    #Dong goi du lieu
                    data = {
                        "url" : current_url,
                        "title": title,
                        "content": text_content
                    }
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    #Danh dau da tham 
                    self.visited_url.add(current_url)
                    count+=1
                    #Lấy các đường dẫn từ trang hiện tại ra cào tiếp
                    for link in soup.find_all('a', href = True):
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




    