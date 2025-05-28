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
        all_codes = re.finall(self.code_pattern, query)
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
                    