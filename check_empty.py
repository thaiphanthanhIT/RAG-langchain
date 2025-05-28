import os

folder_path = "crawl/data/tvpl"
empty_files = []

for filename in os.listdir(folder_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if content == "":
                empty_files.append(filename)

print("Các file không có ký tự nội dung:")
for f in empty_files:
    print(f)
