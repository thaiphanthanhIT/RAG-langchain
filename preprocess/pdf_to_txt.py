import os
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from tabulate import tabulate

# Cấu hình Tesseract (thay đổi đường dẫn nếu dùng Linux/Mac)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ==== CẤU HÌNH THƯ MỤC ====
PDF_DIR = "documents/pdf"
TXT_DIR = "documents/txt"

def clean_text(text: str) -> str:
    """Làm sạch văn bản OCR."""
    if not text:
        return ""
    text = str(text)
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
        r'\n\s*\n': '\n',
    }
    for wrong, correct in replacements.items():
        text = re.sub(wrong, correct, text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

def parse_table(text: str) -> str | None:
    """Tách bảng từ văn bản OCR nếu có."""
    lines = text.split('\n')
    headers = ["STT", "Tên nhóm hồ sơ, tài liệu", "Thời hạn bảo quản", "Ghi chú"]
    table_data = []

    table_pattern = re.compile(
        r'^\s*(\d+)\.\s+(.+?)\s+((?:Vĩnh viễn|\d+\s+năm|Đến khi.*?|Khi ngưng.*?))\s*(.*)?$',
        re.MULTILINE
    )

    for line in lines:
        match = table_pattern.match(line)
        if match:
            stt, name, period, note = match.groups()
            table_data.append([
                clean_text(stt), clean_text(name),
                clean_text(period), clean_text(note or "")
            ])

    return tabulate(table_data, headers=headers, tablefmt="grid") if table_data else None

class PDFOCRProcessor:
    def __init__(self, pdf_path: str, output_path: str, lang="vie+eng", dpi=200):
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.lang = lang
        self.dpi = dpi

    def process_pdf(self):
        try:
            images = convert_from_path(self.pdf_path, dpi=self.dpi)
            full_text = ""

            for idx, image in enumerate(images):
                print(f"📝 OCR Trang {idx + 1}...")
                text = pytesseract.image_to_string(image, lang=self.lang)

                if not text.strip():
                    full_text += f"--- Trang {idx + 1} ---\n[Không có văn bản]\n"
                    continue

                cleaned = clean_text(text)
                parsed_table = parse_table(cleaned)

                content = parsed_table if parsed_table else cleaned
                full_text += f"--- Trang {idx + 1} ---\n{content}\n\n"

            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f"✅ Xong: {self.output_path}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý {self.pdf_path}: {e}")

def convert_all_pdfs(pdf_dir: str, txt_dir: str):
    """
    Chuyển đổi tất cả các file PDF trong thư mục thành file văn bản."""
    os.makedirs(txt_dir, exist_ok=True)

    for file in os.listdir(pdf_dir):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, file)
            output_path = os.path.join(txt_dir, os.path.splitext(file)[0] + ".txt")
            processor = PDFOCRProcessor(pdf_path, output_path)
            processor.process_pdf()

if __name__ == "__main__":
    convert_all_pdfs(PDF_DIR, TXT_DIR)
