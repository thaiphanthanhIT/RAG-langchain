import os
import json 

import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Đường dẫn gốc của dự án
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


API_URL_LAWNET = os.getenv("API_URL_LAWNET")

# Đường dẫn đễn dữ liệu được RAG sử dụng
TEXT_DATA_PATH = os.path.join(PROJECT_ROOT, "crawl/data/tvpl_new/docs")
# Đường dẫn lưu vectorstore
VECTOR_DB_TEXT_PATH = os.path.join(PROJECT_ROOT, "data/vectorstores/db_text")
# Embedding Model
EMBEDDING_MODEL_FILE = os.path.join(PROJECT_ROOT, "data/models/all-MiniLM-L6-v2-f16.gguf")

# OUPUT_DIR của crawlers
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data/documents/crawled_texts")



def set_environment_variables(project_name):
    #filepath = "/app/API.json" # with docker, if you don't use docker, replace by your own filepath to API_key
    filepath = "D:/AI_intern/API.json"
    with open(filepath, 'r', encoding = 'utf-8') as f:
        APIs = json.load(f)
    os.environ['GOOGLE_API_KEY'] = APIs['GOOGLE_API_PVT']
    os.environ['FIREWORKS_API_KEY'] = APIs['FIREWORKS_API_KEY']
    os.environ['GROQ_API_KEY'] = APIs['GROQ_API_KEY']
    os.environ['TAVILY_API_KEY'] = APIs['TAVILY_API_KEY']
    os.environ['LANGCHAIN_API_KEY'] = APIs['LANGCHAIN_API_KEY']
    os.environ['OPENAI_API_KEY'] = APIs['OPEN_ROUTER_API_KEY']
    os.environ['LANGCHAIN_TRACING_V2'] = "true"
    os.environ['LANGCHAIN_PROJECT'] = project_name