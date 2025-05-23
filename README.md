# RAG-langchain: Chatbot AI Tích Hợp RAG

Dự án này xây dựng một chatbot AI tích hợp RAG (Retrieval-Augmented Generation) để trả lời các câu hỏi dựa trên dữ liệu từ Bộ Tài chính và các nguồn tìm kiếm trực tuyến như DuckDuckGo. Chatbot sử dụng các công cụ như LangChain, FAISS, và Google Generative AI (Gemini).

---

## **1. Yêu cầu hệ thống**

### **1.1. Phần mềm**
- Python 3.9 trở lên
- Các thư viện Python (được liệt kê trong `requirements.txt`)

### **1.2. Phần cứng**
- Máy tính có kết nối Internet
- (Tùy chọn) GPU nếu sử dụng mô hình lớn

---

## **2. Hướng dẫn cài đặt**

### **2.1. Clone dự án**
Tải mã nguồn về máy:
```bash
git clone https://github.com/your-repo/RAG-langchain.git
cd RAG-langchain
```

### **2.2 Cài đặt thư viện
Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```
### **2.3 Cấu hình API key Gemini
- Truy cập [Google Generative AI Studio](https://aistudio.google.com/apikey) để lấy API key.
- Tạo file .env trong thư mục gốc của dự án và thêm API key:
```bash
GOOGLE_API_KEY="your-google-api-key"
```
- Nếu muốn chạy crawl thì phải thêm nội dung sau vào file .env (chỗ này lấy trên team, hoặc thay thế bằng cách crawl của Thanh thì không cần)
```bash
API_URL_LAWNET = "" 
```
### **2.4 Tải mô hình Embedding
Tải mô hình [all-MiniLM-L6-v2-f16 từ Hugging Face](https://huggingface.co/caliex/all-MiniLM-L6-v2-f16.gguf/tree/main), đặt file mô hình vào thư mục:
```bash
data/models/
```
## **3. Hướng dẫn chạy dự án

### 3.1. Crawl dữ liệu từ LawNet
Chạy file `nam_crawl.py` để thu thập dữ liệu từ LawNet:  
Dữ liệu sẽ được lưu trong thư mục DEFAULT_OUTPUT_DIR trong file config.py

### 3.2. Khởi tạo Vector DB
Sau khi crawl dữ liệu, chạy file `prepare_vector_DB.py` để tạo cơ sở dữ liệu vector:  
Vector DB sẽ được lưu trong thư mục VECTOR_DB_TEXT_PATHn được custom trong file config.py

### 3.3. Chạy backend (CLI)
Chạy file `qabot.py` để sử dụng chatbot qua giao diện dòng lệnh:  
Nhập câu hỏi của bạn và nhận câu trả lời từ chatbot.
```bash
python qabot.py
```
### 3.4. Chạy frontend (Streamlit)
Chạy file `app.py` để khởi động giao diện Streamlit:  
```bash
streamlit run app.py
```
Lưu ý: chỉ chạy 1 trong hai cái CLI hoặc là Streamlit là được.
