import os
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_text_splitters import CharacterTextSplitter

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Đường dẫn
PDF_DATA_PATH = "crawl/data"
VECTOR_DB_TEXT_PATH = "vectorstores/db_text"
VECTOR_DB_PDF_PATH = "vectorstores/db_pdf"
EMBEDDING_MODEL_FILE = "./all-MiniLM-L6-v2-f16.gguf"

# Tạo vector DB từ văn bản thô
def create_db_from_text():
    try:
        raw_text = """Việt Nam là một quốc gia nằm ở khu vực Đông Nam Á, tiếp giáp với Trung Quốc, Lào và Campuchia. Thủ đô của Việt Nam là Hà Nội, trong khi thành phố lớn nhất là TP. Hồ Chí Minh.

        Địa hình Việt Nam chủ yếu là đồi núi và đồng bằng ven biển. Sông Mekong và sông Hồng là hai con sông lớn nhất.

        Việt Nam có nền văn hóa lâu đời với nhiều di sản văn hóa thế giới như Vịnh Hạ Long, Phố cổ Hội An, và Quần thể Tràng An.

        Kinh tế Việt Nam đang phát triển mạnh, với các ngành mũi nhọn là dệt may, xuất khẩu nông sản và công nghệ thông tin.

        Ẩm thực Việt Nam nổi tiếng với phở, bún chả, bánh mì và cà phê sữa đá.
        """
        logger.info("Bắt đầu tạo vector DB từ văn bản thô.")
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=500, chunk_overlap=50, length_function=len)
        chunks = text_splitter.split_text(raw_text)

        embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
        db = FAISS.from_texts(texts=chunks, embedding=embedding_model)
        db.save_local(VECTOR_DB_TEXT_PATH)
        logger.info(f"[✔] Vector DB từ văn bản đã lưu tại: {VECTOR_DB_TEXT_PATH}")
        return db
    except Exception as e:
        logger.error(f"Lỗi khi tạo vector DB từ văn bản: {e}")
        raise

# Tạo vector DB từ file PDF
def create_db_from_files():
    try:
        logger.info("Bắt đầu tạo vector DB từ file PDF.")
        loader = DirectoryLoader(PDF_DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)

        embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)
        db = FAISS.from_documents(chunks, embedding_model)
        db.save_local(VECTOR_DB_PDF_PATH)
        logger.info(f"[✔] Vector DB từ PDF đã lưu tại: {VECTOR_DB_PDF_PATH}")
        return db
    except Exception as e:
        logger.error(f"Lỗi khi tạo vector DB từ file PDF: {e}")
        raise

# === Thực thi tùy theo mục đích ===
if __name__ == "__main__":
    try:
        # Chạy cái nào tùy bạn muốn
        # create_db_from_text()
        create_db_from_files()
    except Exception as e:
        logger.exception("Đã xảy ra lỗi trong quá trình thực thi.")