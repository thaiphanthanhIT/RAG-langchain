import os
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from tabulate import tabulate

# ⚠️ Đường dẫn tới tesseract.exe trên Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Đường dẫn dữ liệu
PDF_DATA_PATH = "crawl/data/pdf"
TEXT_DATA_PATH = "crawl/data/text"

# Hàm làm sạch văn bản
def clean_text(text):
    """Clean OCR text by fixing common errors and normalizing."""
    if not text:
        return ""
    # Chuyển đổi sang string và loại bỏ ký tự không mong muốn
    text = str(text)
    # Thay thế các ký tự OCR sai phổ biến
    replacements = {
        r'CỌNG HỌ̀': 'CỘNG HÒA',
        r'CHŪ NGHĪA': 'CHỦ NGHĨA',
        r'thời hạan': 'thời hạn',
        r'thời hạn <br>': 'thời hạn ',
        r'bắo quăn': 'bảo quản',
        r'th owned hìg': 'thực hiện',
        r'nhị̂̀u': 'nhiều',
        r'tṛ̣c': 'trực',
        r'\$': '',
        r'Vĩnh viển': 'Vĩnh viễn',
        r'Độc lạp': 'Độc lập',
        r'Hạnh phúc': 'Hạnh phúc',
        r'ngur potatoes': 'người lao động',
        r'l Military': 'lập',
        r'nourse': 'nước',
        r'\n\s*\n': '\n',  # Loại bỏ các dòng trống thừa
    }
    for wrong, correct in replacements.items():
        text = re.sub(wrong, correct, text, flags=re.IGNORECASE)
    # Loại bỏ khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Hàm xử lý bảng từ văn bản OCR
def parse_table(text):
    """Parse text into a table structure if it resembles a table."""
    lines = text.split('\n')
    table_data = []
    headers = ["STT", "Tên nhóm hồ sơ, tài liệu", "Thời hạn bảo quản", "Ghi chú"]
    
    # Regex để phát hiện dòng có cấu trúc bảng (bắt đầu bằng số, theo sau là text)
    table_line_pattern = re.compile(r'^\s*(\d+)\.\s+(.+?)\s+((?:Vĩnh viễn|\d+\s+năm|Đến khi.*?|Khi ngưng.*?))\s*(.*)?$', re.MULTILINE)
    
    for line in lines:
        match = table_line_pattern.match(line)
        if match:
            stt, name, period, note = match.groups()
            table_data.append([clean_text(stt), clean_text(name), clean_text(period), clean_text(note or "")])
    
    if not table_data:
        return None
    # Format bảng bằng tabulate
    return tabulate(table_data, headers=headers, tablefmt="grid")

# Hàm OCR một file PDF
def ocr_pdf_to_txt(pdf_path: str, txt_output_path: str):
    try:
        # Chuyển PDF thành danh sách ảnh (mỗi trang là một ảnh)
        images = convert_from_path(pdf_path, dpi=200)  # Giảm DPI để tăng tốc
        full_text = ""

        for i, image in enumerate(images):
            print(f"📝 Đang OCR trang {i + 1}...")
            # OCR từng ảnh (hỗ trợ tiếng Việt + tiếng Anh)
            text = pytesseract.image_to_string(image, lang='vie+eng')
            if not text.strip():
                print(f"⚠️ Không tìm thấy văn bản ở trang {i + 1}")
                full_text += f"--- Trang {i + 1} ---\n[Không có văn bản]\n"
                continue

            # Làm sạch văn bản
            cleaned_text = clean_text(text)
            
            # Thử parse như bảng
            table = parse_table(cleaned_text)
            if table:
                full_text += f"--- Trang {i + 1} ---\n{table}\n\n"
            else:
                # Văn bản thông thường
                full_text += f"--- Trang {i + 1} ---\n{cleaned_text}\n\n"

        # Lưu text vào file
        with open(txt_output_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"✅ Đã OCR xong: {txt_output_path}")
    except Exception as e:
        print(f"❌ Lỗi OCR cho file {pdf_path}: {e}")

# Hàm xử lý toàn bộ thư mục
def convert_all_pdfs_to_txt(pdf_dir: str, txt_dir: str):
    if not os.path.exists(txt_dir):
        os.makedirs(txt_dir)

    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            txt_output_path = os.path.join(txt_dir, os.path.splitext(filename)[0] + ".txt")
            ocr_pdf_to_txt(pdf_path, txt_output_path)

# Chạy
if __name__ == "__main__":
    convert_all_pdfs_to_txt(PDF_DATA_PATH, TEXT_DATA_PATH)