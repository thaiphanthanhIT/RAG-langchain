### Question Re-writer
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
# LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# Prompt
system = """Bạn là một trình viết lại câu hỏi, có nhiệm vụ chuyển đổi câu hỏi đầu vào thành phiên bản tốt hơn, được tối ưu cho việc truy xuất từ kho vector (vectorstore).
Hãy xem xét câu hỏi đầu vào và cố gắng suy luận về ý định hay ý nghĩa ngữ nghĩa ẩn bên dưới."""
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        (
            "human",
            "Đây là câu hỏi ban đầu: {question}. Hãy diễn đạt lại thành một câu hỏi được cải thiện.",
        ),
    ]
)
question_rewriter = re_write_prompt | llm | StrOutputParser()