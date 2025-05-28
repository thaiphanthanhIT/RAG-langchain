### Router
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Literal
from pydantic import BaseModel, Field
from config import set_environment_variables

set_environment_variables("evaluators")
# Data model
class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "search"] = Field(
        ...,
        description="Given a user question choose to route it to web search or a vectorstore.",
    )

# LLM with function call
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
structured_llm_router = llm.with_structured_output(RouteQuery)

# Prompt
system = """Bạn là một chuyên gia trong việc điều hướng câu hỏi của user tới vectorstore hoặc search.
vectorstore chứa một lượng lớn các văn bản về bộ tài chính.
Sử dụng vectorstore cho các câu hỏi liên quan về thông tư, quyết định... của Bộ Tài chính. Còn lại, sử dụng search"""
route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)
question_router = route_prompt | structured_llm_router