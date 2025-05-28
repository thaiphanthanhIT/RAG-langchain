### Retrieval Grader
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from config import set_environment_variables
import re

set_environment_variables("evaluators")
VECTOR_DB_PATH = "data/vectorstores/db_text"



# Data model
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )
# LLM with function call
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
def json_transform(AImess):
    if "yes" in AImess.content.lower():
        return GradeDocuments(binary_score="yes")
    else:
        return GradeDocuments(binary_score="no")
structured_llm_grader = llm | json_transform
# Prompt
system = """Bạn là người chấm điểm để đánh giá mức độ liên quan của một tài liệu được truy xuất đối với câu hỏi của người dùng.
Nếu tài liệu chứa từ khóa hoặc ý nghĩa ngữ nghĩa liên quan đến câu hỏi, hãy chấm là có liên quan.
Không cần kiểm tra quá nghiêm ngặt. Mục tiêu là loại bỏ các truy xuất sai lệch.
Nếu số hiệu văn bản nằm trong câu hỏi, đó chắc chắc là văn bản liên quan ('yes')
Hãy đưa ra điểm nhị phân 'yes' (có) hoặc 'no' (không) để cho biết liệu tài liệu có liên quan đến câu hỏi hay không.
Ví dụ:
Tài liệu: John yêu thú cưng
Câu hỏi: John có yêu chó không?
Trả lời: yes"""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Retrieved document: \n\n {document} \n\n id_document: {id_document} \n\n User question: {question}"),
    ]
)
embedding_model = GPT4AllEmbeddings(model_file="data/models/all-MiniLM-L6-v2-f16.gguf")
db = FAISS.load_local(VECTOR_DB_PATH, embedding_model, allow_dangerous_deserialization=True)
retriever = db.as_retriever()
retrieval_grader = grade_prompt | structured_llm_grader
if __name__ == "__main__":
    doc0 = """
    | 7.2  | Đổi mới toàn diện việc giải quyết thủ tục hành chính, cung cấp dịch vụ công do Bộ Tài chính quản lý mà không phụ thuộc địa giới hành chính; nâng cao chất lượng dịch vụ công trực tuyến, dịch vụ số cho người dân và doanh nghiệp, hướng tới cung cấp dịch vụ công trực tuyến toàn trình, cá nhân hoá và dựa trên dữ liệu; tăng cường giám sát, đánh giá và trách nhiệm giải trình của cơ quan nhà nước, người có thẩm quyền trong phục vụ Nhân dân.                                                                                                                                                                                                                                            |                                                                                                                                                                                                                               |                                                                                                                                                      |                                                                                                                                                |         |

    |      | Hoàn thành triển khai các dịch vụ công thiết yếu theo Quyết định số 06/QĐ-TTg  ngày 06/01/2022, Quyết định số 422/QĐ-TTg  ngày 04/4/2022, Quyết định số 206/QĐ-TTg  ngày 28/2/2024, kết nối hệ thống giải quyết thủ tục hành chính với hệ thống giám sát đo lường mức độ cung cấp ứng dụng dịch vụ EMC.                                                                                                                                                                                                                                                                                                                                                                                         | Cục CNTT; UBCKNN, Cục Phát triển doanh nghiệp tư nhân và kinh tế tập thể;                                                                                                                                                     |                                                                                                                                                      | Theo thời gian tại Quyết định số 06/QĐ-TTg  ngày 06/01/2022, Quyết định số 422/QĐ-TTg  ngày 04/4/2022, Quyết định số 206/QĐ-TTg ngày 28/2/2024 |         |

    |      | Số hóa hồ sơ, kết quả giải quyết thủ tục hành chính theo quy định của Chính phủ tại Nghị định số 45/2020/NĐ-CP  và Nghị định số 107/2021/NĐ-CP  , đáp ứng yêu cầu kết nối, chia sẻ dữ liệu phục vụ giải quyết thủ tục hành chính, cung cấp dịch vụ công.                                                                                                                                                                                                                                                                                                                                                                                                                                        | Cục CNTT                                                                                                                                                                                                                      | Các đơn vị tiếp nhận và giải quyết TTHC                                                                                                              | Theo thời gian tại tại Nghị định số 45/2020/NĐ-CP và Nghị định số 107/2021/NĐ-CP                                                               |         |
    """
    ques = "Quyết định 1754/QĐ-BTC đề cập đến nội dung gì?"
    ans = retrieval_grader.invoke({"document": doc0, "question": ques})
    x = GradeDocuments.model_validate({"binary_score": "no"})
    print(ans)
    print(x.binary_score)