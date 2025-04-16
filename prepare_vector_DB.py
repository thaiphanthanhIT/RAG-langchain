import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Đường dẫn
TEXT_DATA_PATH = "crawl/data/text"
PDF_DATA_PATH = "crawl/data/pdf"
VECTOR_DB_TEXT_PATH = "vectorstores/db_text"
VECTOR_DB_PDF_PATH = "vectorstores/db_pdf"
EMBEDDING_MODEL_FILE = "./all-MiniLM-L6-v2-f16.gguf"

# Hàm kiểm tra đường dẫn
def validate_path(path: str) -> bool:
    if not os.path.exists(path):
        logger.error(f"Thư mục không tồn tại: {path}")
        return False
    return True

# Hàm xử lý file PDF
def process_pdf_files(pdf_path: str):
    try:
        if not validate_path(pdf_path):
            return None

        logger.info(f"Đang xử lý các file PDF trong thư mục: {pdf_path}")
        loader = DirectoryLoader(pdf_path, glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()

        if not documents:
            logger.warning(f"Không tìm thấy file PDF nào trong thư mục: {pdf_path}")
            return None

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)

        logger.info(f"Đã chia nhỏ {len(chunks)} đoạn văn bản từ file PDF.")
        return chunks
    except Exception as e:
        logger.error(f"Lỗi khi xử lý file PDF: {e}")
        raise

# Hàm xử lý file văn bản
def process_text_files(text_path: str):
    try:
        if not validate_path(text_path):
            return None

        logger.info(f"Đang xử lý các file văn bản trong thư mục: {text_path}")
        # Sử dụng TextLoader với encoding UTF-8
        loader = DirectoryLoader(
            text_path,
            glob="*.txt",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}  # Thêm encoding UTF-8
        )
        documents = loader.load()

        if not documents:
            logger.warning(f"Không tìm thấy file văn bản nào trong thư mục: {text_path}")
            return None

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)

        logger.info(f"Đã chia nhỏ {len(chunks)} đoạn văn bản từ file văn bản.")
        return chunks
    except Exception as e:
        logger.error(f"Lỗi khi xử lý file văn bản: {e}")
        raise

# Tạo vector DB từ văn bản
def create_db_from_text():
    try:
        logger.info("Bắt đầu tạo vector DB từ văn bản.")
        chunks = process_text_files(TEXT_DATA_PATH)
        if not chunks:
            logger.warning("Không có dữ liệu để tạo vector DB từ văn bản.")
            return None

        embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
        db = FAISS.from_documents(chunks, embedding_model)
        os.makedirs(VECTOR_DB_TEXT_PATH, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
        db.save_local(VECTOR_DB_TEXT_PATH)
        logger.info(f"[✔] Vector DB từ văn bản đã lưu tại: {VECTOR_DB_TEXT_PATH}")
        return db
    except Exception as e:
        logger.error(f"Lỗi khi tạo vector DB từ văn bản: {e}")
        raise

# Tạo vector DB từ file PDF
def create_db_from_pdf():
    try:
        logger.info("Bắt đầu tạo vector DB từ file PDF.")
        chunks = process_pdf_files(PDF_DATA_PATH)
        if not chunks:
            logger.warning("Không có dữ liệu để tạo vector DB từ file PDF.")
            return None

        embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
        db = FAISS.from_documents(chunks, embedding_model)
        os.makedirs(VECTOR_DB_PDF_PATH, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
        db.save_local(VECTOR_DB_PDF_PATH)
        logger.info(f"[✔] Vector DB từ PDF đã lưu tại: {VECTOR_DB_PDF_PATH}")
        return db
    except Exception as e:
        logger.error(f"Lỗi khi tạo vector DB từ file PDF: {e}")
        raise

# === Thực thi tùy theo mục đích ===
if __name__ == "__main__":
    try:
        logger.info("Bắt đầu quá trình tạo vector DB...")
        # Tạo vector DB từ văn bản
        create_db_from_text()
        # Tạo vector DB từ file PDF
        # create_db_from_pdf()
        logger.info("Quá trình tạo vector DB hoàn tất.")
    except Exception as e:
        logger.exception("Đã xảy ra lỗi trong quá trình thực thi.")