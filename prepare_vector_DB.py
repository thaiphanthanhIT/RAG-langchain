from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import os

# Đường dẫn
pdf_data_path = "data"
vector_db_text_path = "vectorstores/db_text"
vector_db_pdf_path = "vectorstores/db_pdf"

# Tạo vector DB từ văn bản thô
def create_db_from_text():
    raw_text = """Việt Nam là một quốc gia nằm ở khu vực Đông Nam Á, tiếp giáp với Trung Quốc, Lào và Campuchia. Thủ đô của Việt Nam là Hà Nội, trong khi thành phố lớn nhất là TP. Hồ Chí Minh.

Địa hình Việt Nam chủ yếu là đồi núi và đồng bằng ven biển. Sông Mekong và sông Hồng là hai con sông lớn nhất.

Việt Nam có nền văn hóa lâu đời với nhiều di sản văn hóa thế giới như Vịnh Hạ Long, Phố cổ Hội An, và Quần thể Tràng An.

Kinh tế Việt Nam đang phát triển mạnh, với các ngành mũi nhọn là dệt may, xuất khẩu nông sản và công nghệ thông tin.

Ẩm thực Việt Nam nổi tiếng với phở, bún chả, bánh mì và cà phê sữa đá.
"""
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_text(raw_text)

    embedding_model = GPT4AllEmbeddings(model_file="all-MiniLM-L6-v2-f16.gguf")
    db = FAISS.from_texts(texts=chunks, embedding=embedding_model)
    db.save_local(vector_db_text_path)
    print(f"[✔] Vector DB từ văn bản đã lưu tại: {vector_db_text_path}")
    return db

# Tạo vector DB từ file PDF
def create_db_from_files():
    loader = DirectoryLoader("crawl/data/", glob="*.pdf", loader_cls=PyPDFLoader) 
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    embedding_model = GPT4AllEmbeddings(model_file="all-MiniLM-L6-v2-f16.gguf")
    db = FAISS.from_documents(chunks, embedding_model)
    db.save_local(vector_db_pdf_path)
    print(f"[✔] Vector DB từ PDF đã lưu tại: {vector_db_pdf_path}")
    return db

# === Thực thi tùy theo mục đích ===
if __name__ == "__main__":
    # Chạy cái nào tùy bạn muốn
    # create_db_from_text()
    create_db_from_files()
