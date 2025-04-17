import json


# Đọc lại file JSON
with open("data_test.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# In ra nội dung
print(data[0][1])
