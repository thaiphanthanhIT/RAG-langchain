import os
import re
from typing import List, TypedDict
from langchain.schema import Document

domain_root = "crawl/domain_split_new"
data_path = "crawl/data/tvpl_new/docs"
# ======================= Câu hỏi mẫu cho từng loại =======================
DOMAIN_QUESTION_TEMPLATES = [
    "thể loại", "lĩnh vực", "nhóm văn bản", "phân loại", "loại văn bản", "thể loại văn bản",
    "chuyên mục", "phân vào lĩnh vực", "loại hình", "lưu trong nhóm", "liên quan đến lĩnh vực",
    "nằm trong loại", "áp dụng", "nội dung chính", "phản ánh chuyên đề", "danh mục", "nằm ở thư mục",
    "cấp phân loại", "mục lưu trữ", "dạng văn bản", "nhánh pháp luật", "hạng mục", "ngành quản lý",
    "xếp vào loại", "phân loại theo nhóm", "chuyên mục hành chính", "liên quan đến nhóm chủ đề",
    "loại văn bản chính", "thư mục chứa", "thuộc loại", "thuộc thể loại", "loại gì", "thuộc lĩnh vực",
    "nhóm nào", "xếp vào", "nhánh nào", "áp dụng cho", "lưu trong", "dùng trong", "thư mục nào",
    "dạng gì", "thuộc về", "phản ánh", "nằm ở", "ngành gì", "lĩnh vực gì", "loại"
]

CONTENT_QUESTION_TEMPLATES = [
    "nội dung", "xem chi tiết", "xem văn bản", "xem nội dung", "hiển thị văn bản", "hiện nội dung",
    "toàn bộ văn bản", "chi tiết văn bản", "xem toàn bộ", "đọc văn bản", "đọc toàn văn", "xem đầy đủ",
    "trích dẫn", "xem bản đầy đủ", "xem đầy", "nội dung chi tiết", "nội dung đầy đủ", "toàn văn",
    "hiển thị nội dung", "văn bản gồm những gì", "bao gồm những gì", "xuất ra", "đọc", "ghi ra"
]

SIGNER_QUESTION_TEMPLATES = [
    "ai ký", "người ký", "ký tên", "ký bởi", "ký bởi ai", "chữ ký", "ai là người ký",
    "tên người ký", "người nào ký", "ký", "kí", "ai ban hành", "ai phê duyệt", "người duyệt",
    "ký văn bản", "ký quyết định", "ai ký ban hành"
]

ISSUE_DATE_QUESTION_TEMPLATES = [
    "ngày ban hành", "khi nào ban hành", "ban hành vào ngày nào", "ban hành lúc nào", "ban hành khi nào",
    "thời điểm ban hành", "văn bản có từ khi nào", "ngày có hiệu lực", "có hiệu lực",
    "áp dụng từ ngày nào", "hiệu lực bắt đầu", "thời gian ban hành", "ngày văn bản ban hành",
    "phê duyệt ngày nào", "ra ngày nào", "ngày ra văn bản", "ban hành ngày nào", "xuất bản", "ra đời", 
    "ban hành ngày bao nhiêu"
]

RELATED_DOCS_QUESTION_TEMPLATES = [
    "liên quan đến văn bản nào", "văn bản liên quan", "các văn bản liên quan", "liên quan văn bản nào",
    "tham khảo thêm", "tham chiếu", "dẫn chiếu đến", "văn bản được dẫn", "văn bản nào đi kèm",
    "dẫn đến văn bản nào", "được nhắc đến trong", "văn bản khác liên quan", "gồm những văn bản nào khác",
    "liên quan", "văn bản nào cùng chủ đề", "văn bản được nhắc tới", "tham khảo", "liên văn bản"
]

# =========================== Mẫu mã số văn bản ===========================
CODE_PATTERN = r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    question: str
    generation: str
    documents: List[str]

class DocumentHandler:
    def __init__(self, domain_root, data_path):
        self.domain_root = domain_root
        self.data_path = data_path
        self.code_pattern = CODE_PATTERN
        self.doc_info = self.extract_document_info()

    def extract_document_info(self):
        result = []

        for filename in os.listdir(self.data_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.data_path, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()

                    all_codes = re.findall(CODE_PATTERN, content)
                    main_code = all_codes[0] if all_codes else None
                    related_codes = [c for c in all_codes[1:] if c != main_code]

                    agency = content.split("|")[1].strip() if "|" in content else None

                    issue_date = None
                    for line in lines:
                        if "Số:" in line and "ngày" in line.lower():
                            for part in line.split("|"):
                                if "ngày" in part.lower():
                                    issue_date = part.strip()
                                    break
                        if issue_date:
                            break
                    if not issue_date:
                        for line in lines:
                            if re.search(r"ngày\s+\d{1,2}\s+tháng", line.lower()):
                                issue_date = line.strip()
                                break
                    signer = None
                    for line in reversed(lines):
                        if re.search(r"\b(KT\.|TL\.|THỨ TRƯỞNG|BỘ TRƯỞNG)\b", line):
                            signer = line.strip()
                            break
                        
                result.append({
                    "file": filename,
                    "main_code": main_code,
                    "related_codes": related_codes,
                    "agency": agency,
                    "issue_date": issue_date,
                    "signer": signer,
                    "content": content,
                    "file_path": file_path
                })

        return result

    def find_doc_by_code(self, main_code):
        for doc in self.doc_info:
            if doc['main_code'] == main_code:
                return doc
        return None

    def find_domain_by_main_code(self, main_code):
        for domain_folder in os.listdir(self.domain_root):
            domain_path = os.path.join(self.domain_root, domain_folder)
            if os.path.isdir(domain_path):
                for filename in os.listdir(domain_path):
                    if filename.endswith(".txt"):
                        file_path = os.path.join(domain_path, filename)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            match = re.search(CODE_PATTERN, content)
                            if match and match.group() == main_code:
                                return domain_folder
        return None

    def invoke(self, query):
        question = query["question"]
        match = re.search(CODE_PATTERN, question)
        if not match:
            query["generation"] =  "Không tìm thấy mã văn bản trong câu hỏi."

        main_code = match.group()
        query_lower = question.lower()

        doc = self.find_doc_by_code(main_code)
        if not doc:
            query["generation"] = f"Không tìm thấy văn bản {main_code}."
            query["documents"] = ""
            return query
        src = doc.get("file_path","Not found")
        if src != "Not found":
            query["documents"] = [Document(page_content = doc.get("content","") , metadata = {"source" : src})]

        # Xử lý theo từng loại câu hỏi
        if any(t in query_lower for t in DOMAIN_QUESTION_TEMPLATES):
            domain = self.find_domain_by_main_code(main_code)
            query["generation"] = f"Văn bản {main_code} thuộc thể loại: {domain}" if domain else f"Không xác định được thể loại văn bản {main_code}."

        elif any(t in query_lower for t in SIGNER_QUESTION_TEMPLATES):
            query["generation"] = f"Người ký văn bản {main_code}: {doc['signer'] or 'Không rõ'}"

        elif any(t in query_lower for t in ISSUE_DATE_QUESTION_TEMPLATES):
            query["generation"] = f"Ngày ban hành văn bản {main_code}: {doc['issue_date'] or 'Không rõ'}"

        elif any(t in query_lower for t in RELATED_DOCS_QUESTION_TEMPLATES):
            query["generation"] = f"Văn bản {main_code} liên quan đến: {', '.join(doc['related_codes'])}" if doc['related_codes'] else "Không tìm thấy văn bản liên quan."
        else:
            query["generation"] = "Dưới đây là nội dung văn bản:"
        
        return query

search = DocumentHandler(domain_root, data_path)

# ================================ SỬ DỤNG ================================
if __name__ == "__main__":
<<<<<<< HEAD:models/manual_query/manual_search.py
    handler = DocumentHandler(domain_root, data_path)

    # Ví dụ câu hỏi
    question = "Ai là người ký 1736/QĐ-BTC"
    query = {"question": question, "generation": "", "documents": []}
    print(handler.invoke(query))
=======
    domain_root = r"F:\TinHoc\BinningMini\RAG + langchain\RAG-langchain\crawl\domain_split"
    data_path = r"F:\TinHoc\BinningMini\RAG + langchain\RAG-langchain\crawl\data\tvpl"

    handler = DocumentHandler(domain_root, data_path)

    # Ví dụ câu hỏi
    questions = [
        "ai là người kí nghị định 1524/QĐ-BTC"
    ]
>>>>>>> 950159bc90c515f7c9aacf56d057baecda80fe12:query domain.py

