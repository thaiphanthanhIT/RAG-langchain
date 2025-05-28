### Hallucination Grader
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
# Data model
class GradeHallucinations(BaseModel):
    """Điểm nhị phân cho việc có hiện tượng ảo giác trong câu trả lời được sinh ra."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )
# LLM with function call
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
def json_transform(AImess):
    if "yes" in AImess.content.lower():
        return GradeHallucinations(binary_score="yes")
    else:
        return GradeHallucinations(binary_score="no")
structured_llm_grader = llm | json_transform
# Prompt
system = """Bạn là người chấm điểm để đánh giá liệu câu trả lời do mô hình ngôn ngữ lớn (LLM) tạo ra có dựa trên hay được hỗ trợ bởi tập hợp các dữ kiện đã truy xuất hay không.
Hãy đưa ra điểm nhị phân 'yes' (có) hoặc 'no' (không).
'Yes' có nghĩa là câu trả lời có căn cứ hay được hỗ trợ bởi tập hợp các dữ kiện đó. """
hallucination_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"),
    ]
)
hallucination_grader = hallucination_prompt | structured_llm_grader