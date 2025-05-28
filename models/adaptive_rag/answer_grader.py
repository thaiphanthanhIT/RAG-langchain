### Answer Grader
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
# Data model
class GradeAnswer(BaseModel):
    """Điểm nhị phân để đánh giá mức độ câu trả lời đáp ứng câu hỏi."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )


# LLM with function call
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
def json_transform(AImess):
    if "yes" in AImess.content.lower():
        return GradeAnswer(binary_score="yes")
    else:
        return GradeAnswer(binary_score="no")
structured_llm_grader = llm | json_transform

# Prompt
system = """You are a grader assessing whether an answer addresses / resolves a question \n 
     Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question."""
answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)
answer_grader = answer_prompt | structured_llm_grader