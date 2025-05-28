from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import ChatPromptTemplate
from config import set_environment_variables
from question_rewrite import question_rewriter
from search_tool import web_search_tool

set_environment_variables("evaluators")
VECTOR_DB_PATH = "data/vectorstores/db_text"
EMBEDDING_MODEL_FILE = "data/models/all-MiniLM-L6-v2-f16.gguf"
embedding_model = GPT4AllEmbeddings(model_file=EMBEDDING_MODEL_FILE)

db = FAISS.load_local(
    folder_path=VECTOR_DB_PATH,
    embeddings=embedding_model,
    allow_dangerous_deserialization=True
)
vectorstore = db
retriever = vectorstore.as_retriever()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
)

class GradeDocuments(BaseModel):
    """Chấm điểm nhị phân cho tài liệu có liên quan đến câu hỏi hoặc khôngkhông."""

    binary_score: str = Field(
        description="Tài liệu có liên quan đến câu hỏi, 'có' hoặc 'không'"
    )
def json_transform(AImess):
    if "yes" in AImess.content.lower():
        return GradeDocuments(binary_score="yes")
    else:
        return GradeDocuments(binary_score="no")
structured_llm_grader = llm | json_transform

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)


# Prompt
system = """Bạn là người chấm điểm đánh giá mức độ liên quan của một tài liệu đã truy xuất với câu hỏi của người dùng. \n
Nếu tài liệu chứa từ khóa hoặc ý nghĩa, ngữ nghĩa liên quan đến câu hỏi, hãy chấm điểm là có liên quan. \n
Đưa ra điểm nhị phân 'có' hoặc 'không' để chỉ ra liệu tài liệu có liên quan đến câu hỏi hay không. 
Nếu id_documents xuất hiện trong question, đáp án chắc chắn là 'có'.
Ví dụ: John yêu các loài vật
Câu hỏi: John yêu chó không? 
Trả lời: có """
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Tài liệu đã truy vấn : \n\n {document} \n\n id_documents: {id_document} \n\n Câu hỏi của người dùng: {question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader

def test_with_custom_question():
    question = input("Nhập câu hỏi bất kỳ: ")
    docs = retriever.invoke(question)
    # Lọc tất cả tài liệu liên quan
    relevant_docs = []
    for d in docs:
        ans = retrieval_grader.invoke({"question": question, "document": d.page_content})
        if ans.binary_score.lower() == "có":
            relevant_docs.append(d)
    if relevant_docs:
        print(f"Có {len(relevant_docs)} tài liệu liên quan.")
        from generate import rag_chain
        answer = rag_chain.invoke({"context": relevant_docs, "question": question})
        print("\n--- Câu trả lời chi tiết từ tài liệu ---")
        print(answer)
        return
    else:
        print("Không có tài liệu liên quan.")

    print("\n--- Câu hỏi sau khi viết lại ---")
    result = question_rewriter.invoke({"question": question})
    print(result)

    print("\n--- Kết quả tìm kiếm web ---")
    results = web_search_tool.run(question)
    for i, result in enumerate(results):
        print(f"[{i+1}] {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['content']}\n")
