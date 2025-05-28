from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
from pydantic import BaseModel, Field
from config import VECTOR_DB_TEXT_PATH, TEXT_DATA_PATH, EMBEDDING_MODEL_FILE
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import ChatPromptTemplate
import config
# from langchain_openai import OpenAIEmbeddings

embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)

db = FAISS.load_local(
    folder_path=VECTOR_DB_TEXT_PATH,
    embeddings=embedding_model,
    allow_dangerous_deserialization=True
)
vectorstore = db
retriever = vectorstore.as_retriever()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=config.GOOGLE_API_KEY  
)

class GradeDocuments(BaseModel):
    """Chấm điểm nhị phân cho tài liệu có liên quan đến câu hỏi hoặc khôngkhông."""

    binary_score: str = Field(
        description="Tài liệu có liên quan đến câu hỏi, 'có' hoặc 'không'"
    )

structured_llm_grader = llm.with_structured_output(GradeDocuments)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)

# Prompt
system = """Bạn là người chấm điểm đánh giá mức độ liên quan của một tài liệu đã truy xuất với câu hỏi của người dùng. \n
Nếu tài liệu chứa từ khóa hoặc ý nghĩa, ngữ nghĩa liên quan đến câu hỏi, hãy chấm điểm là có liên quan. \n
Đưa ra điểm nhị phân 'có' hoặc 'không' để chỉ ra liệu tài liệu có liên quan đến câu hỏi hay không."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Tài liệu đã truy vấn : \n\n {document} \n\n Câu hỏi của người dùng: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader
question = "Thông tin chi tiết hướng dẫn chế độ tài chính cho các ngân hàng và tổ chức tài chính tại Việt Nam"
docs = retriever.invoke(question)
if docs:
    doc_txt = docs[0].page_content
    ans = retrieval_grader.invoke({"question": question, "document": doc_txt})
    print("Có tài liệu liên quan:")
else:
    print("Không có tài liệu liên quan.")