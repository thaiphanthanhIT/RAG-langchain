import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
import sys
# Thêm thư mục gốc của dự án vào sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)
from config import TEXT_DATA_PATH, VECTOR_DB_TEXT_PATH, EMBEDDING_MODEL_FILE

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def validate_path(path: str) -> bool:
    if not os.path.exists(path):
        logger.error(f"❌ Thư mục không tồn tại: {path}")
        return False
    return True

def process_text_files(text_path: str):
    if not validate_path(text_path):
        return []

    logger.info(f"📄 Đang xử lý các file văn bản trong: {text_path}")
    loader = DirectoryLoader(
        text_path,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    if not documents:
        logger.warning("⚠ Không tìm thấy file văn bản nào.")
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size=4096, chunk_overlap=1024)
    chunks = splitter.split_documents(documents)
    logger.info(f"✅ Đã chia nhỏ thành {len(chunks)} đoạn văn bản.")
    return chunks

def create_db_from_text(text_path: str = TEXT_DATA_PATH, db_path: str = VECTOR_DB_TEXT_PATH):
    try:
        logger.info("🚀 Bắt đầu tạo vector DB từ văn bản...")
        chunks = process_text_files(text_path)
        if not chunks:
            logger.warning("⚠ Không có dữ liệu để tạo vector DB.")
            return None

        embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
        db = FAISS.from_documents(chunks, embedding_model)
        os.makedirs(db_path, exist_ok=True)
        db.save_local(db_path)
        logger.info(f"[✔] Vector DB đã lưu tại: {db_path}")
        return db
    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo vector DB: {e}")
        raise

# Thực thi trực tiếp
if __name__ == "__main__":
    create_db_from_text()