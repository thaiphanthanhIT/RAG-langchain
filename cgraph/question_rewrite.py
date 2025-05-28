from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import config

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=config.GOOGLE_API_KEY
)

# Prompt
system = """Bạn là người viết lại câu hỏi, chuyển đổi câu hỏi đầu vào thành phiên bản tốt hơn được tối ưu hóa \n
cho tìm kiếm trên web. Hãy xem đầu vào và cố gắng lý giải về ý định / ý nghĩa ngữ nghĩa cơ bản."""
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Đây là câu hỏi đầu tiên: \n\n {question} \n Xây dựng một câu hỏi cải tiến.",
        ),
    ]
)

question_rewriter = re_write_prompt | llm | StrOutputParser()
