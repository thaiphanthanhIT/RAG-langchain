import re
import os

class Search:
    def __init__(self, data_path, regex = r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"):
        self.path = data_path
        self.code_pattern = regex
    def extract_main_code(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            all_codes = re.findall(self.code_pattern, content)
            return all_codes[0] if all_codes else None
    def search(self, query)->list:
        all_codes = re.findall(self.code_pattern, query)
        contents = []
        for filename in os.listdir(self.path):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.path, filename)
                main_code = self.extract_main_code(file_path)
                if main_code and main_code in all_codes:
                    print(f"Document {main_code} found.")
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        contents.append(content)
                        if len(contents) == len(all_codes):
                            break
        return contents

s = Search(r"F:\TinHoc\BinningMini\RAG + langchain\crawl\data\tvpl")

query = "What is the name of the 01/2022/TT-BTC"
matched_docs = s.search(query)

for i, doc in enumerate(matched_docs, 1):
    print(f"\n--- Document {i} ---\n")
    print(doc[:1000])  # In 1000 ký tự đầu


# import os
# import re
# import json
#
# # ==== Phần 1: In main_code từ file JSON (tức là code của mỗi domain) ====
#
# json_path = r'F:\TinHoc\BinningMini\RAG + langchain\links.json'
# code_pattern = r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"
#
# print("===== MAIN CODE từ JSON (theo DOMAIN) =====")
# with open(json_path, 'r', encoding='utf-8') as f:
#     json_data = json.load(f)
#
# code_to_domain = {}
#
# for item in json_data:
#     name = item.get("name", "")
#     link = item.get("link", "")
#     match_code = re.search(code_pattern, name)
#     match_domain = re.search(r'/van-ban/([^/]+)/', link)
#
#     if match_code and match_domain:
#         main_code = match_code.group(0)
#         domain = match_domain.group(1)
#         code_to_domain[main_code] = domain
#         print(f"+ Mã: {main_code}  →  Domain: {domain}")
# print()
#
#
# # ==== Phần 2: In main_code từ từng file văn bản .txt ====
#
# def extract_main_code(file_path):
#     with open(file_path, 'r', encoding='utf-8') as f:
#         content = f.read()
#         all_codes = re.findall(code_pattern, content)
#         return all_codes[0] if all_codes else None
#
#
# txt_folder = r"F:\TinHoc\BinningMini\RAG + langchain\crawl\data\tvpl"
#
# print("===== MAIN CODE từ file .txt =====")
# for filename in os.listdir(txt_folder):
#     if filename.endswith(".txt"):
#         file_path = os.path.join(txt_folder, filename)
#         main_code = extract_main_code(file_path)
#         print(f"+ {filename}: {main_code}")

import os
import re
from sklearn.metrics import precision_score, recall_score, f1_score

# Class Search từ trước
class Search:
    def __init__(self, data_path, regex=r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"):
        self.path = data_path
        self.code_pattern = regex

    def extract_main_code(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            all_codes = re.findall(self.code_pattern, content)
            return all_codes[0] if all_codes else None

    def search(self, query) -> list:
        all_codes = re.findall(self.code_pattern, query)
        contents = []
        for filename in os.listdir(self.path):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.path, filename)
                main_code = self.extract_main_code(file_path)
                if main_code and main_code in all_codes:
                    print(f"✅ Tìm thấy văn bản {main_code}.")
                    with open(file_path, "r", encoding="utf-8") as f:
                        contents.append(f.read())
                    if len(contents) == len(all_codes):
                        break
        return contents

# 🧠 Tạo câu hỏi tiếng Việt từ main_code
def generate_vietnamese_queries_from_folder(folder_path, code_pattern):
    templates = [
        "Tìm văn bản có số hiệu {}",
        "Văn bản pháp luật {} nói về vấn đề gì?",
        "Thông tin chi tiết về văn bản {} là gì?",
        "Văn bản {} được ban hành khi nào?",
        "Nội dung chính của văn bản {} là gì?",
        "Cho tôi xem văn bản {}",
        "Văn bản có mã {} là văn bản gì?",
        "Văn bản {} được ai ban hành?",
        "Ai là người ký văn bản {}?",
        "Văn bản {} thuộc lĩnh vực gì?"
    ]

    queries = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                match = re.findall(code_pattern, content)
                if match:
                    main_code = match[0]
                    for template in templates:
                        query = template.format(main_code)
                        queries.append((query, main_code))
    return queries

# 🎯 Hàm đánh giá hệ thống
def evaluate_search_system(searcher, queries_with_labels, max_test=100):
    y_true = []
    y_pred = []

    for idx, (query, expected_code) in enumerate(queries_with_labels):
        if idx >= max_test:
            break
        results = searcher.search(query)
        found = any(expected_code in doc for doc in results)

        y_true.append(1)
        y_pred.append(1 if found else 0)

    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    return precision, recall, f1

# 🧪 Chạy kiểm thử
if __name__ == "__main__":
    folder_path = r"F:\TinHoc\BinningMini\RAG + langchain\crawl\data\tvpl"
    code_pattern = r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"

    searcher = Search(folder_path, regex=code_pattern)

    print("🔄 Đang sinh câu hỏi từ dữ liệu...")
    queries = generate_vietnamese_queries_from_folder(folder_path, code_pattern)

    print(f"✅ Sinh được {len(queries)} câu hỏi.")

    print("📊 Đang đánh giá hệ thống tìm kiếm...")
    precision, recall, f1 = evaluate_search_system(searcher, queries, max_test=100)

    print(f"\n🎯 Kết quả đánh giá trên {min(len(queries), 100)} query:")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1-score: {f1:.2f}")
    print(queries)

