import os
import re
import json
import shutil

# ======== Bước 1: Nạp JSON và ánh xạ main_code -> list domain ========
json_path = r'F:\TinHoc\BinningMini\RAG + langchain\RAG-langchain\crawl\data\links.json'
with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

code_pattern = r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"
code_to_domains = {}

for item in json_data:
    name = item.get("name", "")
    link = item.get("link", "")
    match_code = re.search(code_pattern, name)
    match_domain = re.search(r'/van-ban/([^/]+)/', link)
    if match_code and match_domain:
        code = match_code.group(0)
        domain = match_domain.group(1)
        if code in code_to_domains:
            if domain not in code_to_domains[code]:
                code_to_domains[code].append(domain)
        else:
            code_to_domains[code] = [domain]

# ======== Bước 2: Lấy code đầu tiên trong file txt ========
def extract_main_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        all_codes = re.findall(code_pattern, content)
        return all_codes[0] if all_codes else None

# ======== Bước 3: Copy file vào tất cả folder domain ứng với code đầu tiên ========
txt_folder = r"F:\TinHoc\BinningMini\RAG + langchain\RAG-langchain\crawl\data\tvpl_new\docs"
output_root = r"F:\TinHoc\BinningMini\RAG + langchain\RAG-langchain\crawl\domain_split_new"

for filename in os.listdir(txt_folder):
    if filename.endswith(".txt"):
        file_path = os.path.join(txt_folder, filename)
        main_code = extract_main_code(file_path)

        if main_code and main_code in code_to_domains:
            domains = code_to_domains[main_code]
            for domain in domains:
                domain_folder = os.path.join(output_root, domain)
                os.makedirs(domain_folder, exist_ok=True)
                shutil.copy(file_path, os.path.join(domain_folder, filename))
            print(f"✓ Đã chuyển {filename} → các domain: {', '.join(domains)}")
        else:
            print(f"✗ Không tìm thấy domain cho: {filename} (code: {main_code})")
