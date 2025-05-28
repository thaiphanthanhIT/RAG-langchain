import os
import re
import json
import shutil

# ======== Bước 1: Nạp JSON và ánh xạ main_code -> domain ========
json_path = r'demo/crawl/data/tvpl/links.json'
with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

code_pattern = r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"
code_to_domain = {}

for item in json_data:
    name = item.get("name", "")
    link = item.get("link", "")
    match_code = re.search(code_pattern, name)
    match_domain = re.search(r'/van-ban/([^/]+)/', link)
    if match_code and match_domain:
        code_to_domain[match_code.group(0)] = match_domain.group(1)

# ======== Bước 2: Tìm main_code trong các file txt ========
def extract_main_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        all_codes = re.findall(code_pattern, content)
        return all_codes[0] if all_codes else None

# # ======== Bước 3: Di chuyển file txt vào thư mục theo domain ========
txt_folder = r"demo/crawl/data/tvpl/docs"
output_root = r"demo/crawl/data/domains"
set_domains = set()
for filename in os.listdir(txt_folder):
    if filename.endswith(".txt"):
        file_path = os.path.join(txt_folder, filename)
        main_code = extract_main_code(file_path)

        if main_code and main_code in code_to_domain:
            domain = code_to_domain[main_code]
            set_domains.add(domain)
            domain_folder = os.path.join(output_root, domain)
            os.makedirs(domain_folder, exist_ok=True)

            shutil.copy(file_path, os.path.join(domain_folder, filename))
            print(f"✓ Đã chuyển {filename} → {domain}")
        else:
            print(f"✗ Không tìm thấy domain cho: {filename} (code: {main_code})")

with open('demo/crawl/data/domains.json', 'w', encoding='utf=8') as f: 
    json.dump(list(set_domains), f)
    print("Save list of domains successfully")