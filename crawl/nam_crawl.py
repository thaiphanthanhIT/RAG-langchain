import requests
from bs4 import BeautifulSoup
import os
import json
import time
from dotenv import load_dotenv
load_dotenv()

# Giới hạn số page crawl
max_pages = 10

# API endpoint và thông tin xác thực
api_url = os.getenv("API_URL_LAWNET")
base_url = "https://lawnet.vn"

# Body mẫu cho yêu cầu POST
body_template = {
    "SearchModelType": 0,
    "Title": "LawNet-Tài chính",
    "page": 1,
    "DescEN": None,
    "DescVN": "Là trang thông tin văn bản về lĩnh vực tài chính tại việt nam, tìm kiếm văn bản về luật tài chính tại việt nam 2025",
    "KeywordEN": None,
    "KeywordVN": "Tài chính, văn bản tài chính, luật tài chính việt nam, luật về tài chính ở việt nam, pháp luật về tài chính của việt nam, văn bản luật tài chính của việt nam, luật tài chính của việt nam",
    "keyword": None,
    "area": None,
    "lan": 1,
    "match": False,
    "matchTemp": False,
    "type": -1,
    "typeTemp": None,
    "field": 10,
    "organ": None,
    "status": "",
    "bday": "17/04/1945",
    "eday": "17/04/2025",
    "bdayCHL": None,
    "edayCHL": None,
    "sort": "0",
    "signer": None,
    "isscan": None,
    "istranslated": None
}

# Thư mục để lưu các file .txt
output_dir = "crawled_texts"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Hàm crawl và lưu nội dung từ URL
def crawl_and_save(url, output_dir):
    try:
        full_url = base_url + url
        print(f"Crawling: {full_url}")

        # Gửi yêu cầu GET với header để giả lập trình duyệt
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(full_url, headers=headers)
        response.raise_for_status()

        # Phân tích HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trích xuất text từ các thẻ <p> và <td> (dựa trên cấu trúc HTML bạn cung cấp)
        text_content = []
        for element in soup.find_all(['p', 'td']):
            text = element.get_text(separator=' ', strip=True)
            if text:
                text_content.append(text)

        # Kết hợp các dòng text, loại bỏ dòng trống
        final_text = '\n'.join(line for line in text_content if line.strip())

        # Tạo tên file từ URL
        file_name = url.replace('/', '_').replace('.html', '.txt')
        file_path = os.path.join(output_dir, file_name)

        # Lưu nội dung vào file .txt
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        print(f"Saved to: {file_path}")

    except requests.RequestException as e:
        print(f"Error crawling {full_url}: {e}")
    except Exception as e:
        print(f"Error processing {full_url}: {e}")

# Hàm gửi yêu cầu POST và xử lý response
def fetch_documents(page):
    body = body_template.copy()
    body["page"] = page

    try:
        response = requests.post(api_url, json=body)
        response.raise_for_status()
        data = response.json()

        if "Data" in data and "Documents" in data["Data"]:
            return data["Data"]["Documents"], data["Data"]["TotalItems"]
        else:
            print(f"No documents found on page {page}")
            return [], 0

    except requests.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        return [], 0

# Main logic
def main():
    page = 1
    total_items = float('inf')  # Sẽ cập nhật sau lần gọi API đầu tiên

    while True:
        if page > max_pages:
            print("Reached the maximum number of pages to crawl.")
            break

        print(f"Fetching page {page}...")
        documents, total_items_response = fetch_documents(page)

        if not documents:
            print("No more documents to fetch.")
            break

        if page == 1:
            total_items = total_items_response
            print(f"Total items to fetch: {total_items}")

        # Trích xuất và crawl từng DocumentUrl
        for doc in documents:
            document_url = doc.get("DocumentUrl")
            if document_url:
                crawl_and_save(document_url, output_dir)
                time.sleep(1)  # Nghỉ 1 giây để tránh bị chặn

        # Kiểm tra xem còn trang nào nữa không
        if page * len(documents) >= total_items:
            print("Reached the last page.")
            break

        page += 1
        time.sleep(2)  # Nghỉ 2 giây giữa các yêu cầu API

if __name__ == "__main__":
    main()