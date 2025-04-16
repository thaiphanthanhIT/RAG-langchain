import os
from PyPDF2 import PdfReader

# Đường dẫn thư mục
PDF_DATA_PATH = "crawl/data/pdf"
TEXT_DATA_PATH = "crawl/data/text"

# Hàm chuyển PDF sang TXT
def pdf_to_txt(pdf_path: str, txt_output_path: str):
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        
        # Trích xuất text từ từng trang
        for page in reader.pages:
            text = page.extract_text()
            if text:  # Kiểm tra nếu trang có nội dung
                full_text += text + "\n"
        
        # Lưu text vào file với encoding UTF-8
        with open(txt_output_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(full_text)
        print(f"Đã chuyển PDF sang TXT: {txt_output_path}")
        
    except Exception as e:
        print(f"Lỗi khi chuyển PDF sang TXT: {e}")

# Hàm chuyển tất cả file PDF trong thư mục
def convert_all_pdfs_to_txt(pdf_dir: str, txt_dir: str):
    if not os.path.exists(txt_dir):
        os.makedirs(txt_dir)  # Tạo thư mục nếu chưa tồn tại

    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            txt_output_path = os.path.join(txt_dir, os.path.splitext(filename)[0] + ".txt")
            pdf_to_txt(pdf_path, txt_output_path)

# Thực thi chuyển đổi
if __name__ == "__main__":
    convert_all_pdfs_to_txt(PDF_DATA_PATH, TEXT_DATA_PATH)