import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)
from config import API_URL_LAWNET, DEFAULT_OUTPUT_DIR

# Constants
BASE_URL = "https://lawnet.vn"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
}
DEFAULT_MAX_PAGES = 10
DEFAULT_OUTPUT_DIR = "data/lawnet_documents"
def build_request_body(page: int) -> dict:
    """Tạo body cho request POST"""
    return {
        "SearchModelType": 0,
        "Title": "LawNet-Tài chính",
        "page": page,
        "DescEN": None,
        "DescVN": None,
        "KeywordEN": None,
        "KeywordVN": None,
        "keyword": None,
        "area": None,
        "lan": 1,
        "match": False,
        "matchTemp": False,
        "type": -1,
        "typeTemp": None,
        "field": None,
        "organ": None,
        "status": "",
        "bday": "01/01/2022",
        "eday": "17/04/2025",
        "bdayCHL": None,
        "edayCHL": None,
        "sort": "0",
        "signer": None,
        "isscan": None,
        "istranslated": None
    }


def fetch_documents_from_api(page: int) -> tuple[list, int]:
    """Gửi POST request và trả về danh sách tài liệu + tổng số tài liệu"""
    try:
        body = build_request_body(page)
        response = requests.post(API_URL_LAWNET, json=body, timeout=10)
        response.raise_for_status()
        data = response.json()
        documents = data.get("Data", {}).get("Documents", [])
        total_items = data.get("Data", {}).get("TotalItems", 0)
        return documents, total_items
    except Exception as e:
        print(f"[ERROR] Fetching page {page} failed: {e}")
        return [], 0


def extract_text_from_html(html: str) -> str:
    """Trích xuất văn bản chính từ HTML"""
    soup = BeautifulSoup(html, 'html.parser')

    main_content = soup.select_one('div#divContent') or soup.select_one('div.docContent')

    if not main_content:
        main_content = soup.body

    elements = main_content.find_all(['p', 'td']) if main_content else []
    texts = [el.get_text(separator=' ', strip=True) for el in elements if el.get_text(strip=True)]
    return '\n'.join(texts)



def crawl_document_and_save(relative_url: str, output_dir: str) -> str | None:
    """Crawl nội dung văn bản từ URL và lưu thành file .txt"""
    full_url = BASE_URL + relative_url
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        text = extract_text_from_html(response.text)

        os.makedirs(output_dir, exist_ok=True)
        file_name = relative_url.replace('/', '_').replace('.html', '.txt')
        file_path = os.path.join(output_dir, file_name)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"[SUCCESS] Saved: {file_path}")
        return file_path
    except Exception as e:
        print(f"[ERROR] Crawling {full_url} failed: {e}")
        return None


def crawl_lawnet_documents(max_pages: int = DEFAULT_MAX_PAGES, output_dir: str = DEFAULT_OUTPUT_DIR):
    """Hàm chính để crawl toàn bộ tài liệu"""
    page = 1
    total_items = float('inf')

    while page <= max_pages:
        print(f"\n[INFO] Fetching page {page}...")
        documents, total_items_response = fetch_documents_from_api(page)

        if not documents:
            print("[INFO] No documents returned.")
            break

        if page == 1:
            total_items = total_items_response
            print(f"[INFO] Total documents: {total_items}")

        for doc in documents:
            url = doc.get("DocumentUrl")
            if url:
                crawl_document_and_save(url, output_dir)
                time.sleep(0.001)  # tránh bị chặn IP

        if page * len(documents) >= total_items:
            print("[INFO] All documents fetched.")
            break

        page += 1
        time.sleep(2)


if __name__ == "__main__":
    crawl_lawnet_documents()
