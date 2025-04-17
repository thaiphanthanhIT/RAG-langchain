import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Đường dẫn gốc của dự án
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


API_URL_LAWNET = os.getenv("API_URL_LAWNET")

# Đường dẫn đễn dữ liệu được RAG sử dụng
TEXT_DATA_PATH = os.path.join(PROJECT_ROOT, "data/documents/lawnet_txt")
# Đường dẫn lưu vectorstore
VECTOR_DB_TEXT_PATH = os.path.join(PROJECT_ROOT, "data/vectorstores/db_text")
# Embedding Model
EMBEDDING_MODEL_FILE = os.path.join(PROJECT_ROOT, "data/models/all-MiniLM-L6-v2-f16.gguf")

# OUPUT_DIR của crawlers
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/documents/crawled_texts")


