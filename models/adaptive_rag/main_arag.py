from langgraph.graph import StateGraph
from langchain.schema import Document
from typing import TypedDict, List, Tuple
from dotenv import load_dotenv
import logging
import os
from .route_query import question_router
from .retrieve_grader import retrieval_grader, retriever
from .generate import rag_chain
from .answer_grader import answer_grader
from .question_rewriter import question_rewriter
from .hallucination_grader import hallucination_grader
from .search import web_search_tool
from .config import set_environment_variables

import re 

from config import set_environment_variables

set_environment_variables("evaluators")


code_pattern = r"\d{1,4}/(?:\d{4}/)?[A-ZĐ]{1,5}(?:-[A-Z0-9]{1,5})*"
def extract_main_code(docs):
    all_codes = []
    for doc in docs: 
        text = doc.page_content if hasattr(doc, "page_content") else str(doc)
        codes = re.findall(code_pattern, text)
        if codes:    
            all_codes.append(codes[0])
    return all_codes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
VECTOR_DB_PATH = "data/vectorstores/db_text"
MAX_WEB_RESULTS = 4
MODEL_GEMINI = "gemini-1.5-flash"  # Sử dụng model hợp lệ

# Load Gemini API key từ file .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("API key GOOGLE_API_KEY chưa được thiết lập trong môi trường hoặc file .env.")


### Graph
from typing import List

from typing_extensions import TypedDict


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
    retry_count: int
    history: List[Tuple[str, str, List[str]]] 

def retrieve(state):
    """
    Truy xuất tài liệu

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        state (dict): Thêm khóa mới vào state, tên là "documents", chứa các tài liệu đã được truy xuất

    """
    print("---RETRIEVE---")
    question = state["question"]

    # Retrieval
    documents = retriever.invoke(question) 
    state["documents"] = documents
    # id_documents = extract_main_code(documents)
    return state


def generate(state):
    """
    Tạo câu trả lời

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        state (dict): Thêm khóa mới vào state, tên là "generation", chứa kết quả sinh ra từ mô hình ngôn ngữ (LLM)

    """
    state["retry_count"] = state.get("retry_count", 0) + 1
    print(f"retry_count: {state["retry_count"]}")
    if state["retry_count"] > 4:
        print("---DECISION: QUÁ SỐ LẦN THỬ, CHUYỂN SANG TÌM KIẾM TRÊN WEB---")
        state["route"] = "reach_limit"
        return state
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    state["generation"] = generation
    return state

def web_generate(state):
    """
    Tạo câu trả lời

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        state (dict): Thêm khóa mới vào state, tên là "generation", chứa kết quả sinh ra từ mô hình ngôn ngữ (LLM)

    """
    print("---GENERATE FROM WEB---")
    question = state["question"]
    documents = state["documents"]

    # content generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    state["generation"] = generation
    return state

def grade_documents(state):
    """
    Xác định liệu các tài liệu được truy xuất có liên quan đến câu hỏi hay không.

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        state (dict): Cập nhật khóa "documents" chỉ với các tài liệu liên quan đã được lọc

    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    # Score each doc
    filtered_docs = []
    for i, d in enumerate(documents):
        id_doc = extract_main_code(d)
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content, "id_document": id_doc}
        )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    state["documents"] = filtered_docs 
    return state
    #return {"documents": filtered_docs, "question": question}


def transform_query(state):
    """
    Chuyển câu hỏi thành 1 câu hỏi khác (bằng tiếng việt) dễ tìm kiếm thông tin hơn.
    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        state (dict): Cập nhật khóa "question" với câu hỏi đã được diễn đạt lại
    """
    state["retry_count"] = state.get("retry_count", 0) + 1
    print(f"retry_count: {state["retry_count"]}")
    if state["retry_count"] > 5:
        print("---DECISION: QUÁ SỐ LẦN THỬ, CHUYỂN SANG TÌM KIẾM TRÊN WEB---")
        state["route"] = "reach_limit"
        return state
    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]

    # Re-write question
    better_question = question_rewriter.invoke({"question": question})
    state["question"] = better_question
    return state
    #return {"documents": documents, "question": better_question}


def web_search(state):
    """
    Tìm kiếm web dựa trên câu hỏi đã được diễn đạt lại.

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        state (dict): Cập nhật khóa "documents" bằng cách nối thêm các kết quả từ web

    """

    print("---WEB SEARCH---")
    question = state["question"]

    # Web search
    docs = web_search_tool.invoke({"query": question})
    web_results = "\n".join([d["content"] for d in docs])
    web_results = Document(page_content=web_results)
    state["documents"] = web_results
    return state
    #return {"documents": web_results, "question": question}


### Edges ###


def route_question(state):
    """
    Điều hướng câu hỏi đến tìm kiếm web hoặc RAG.

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        str: Nút tiếp theo cần gọi

    """

    print("---ROUTE QUESTION---")
    question = state["question"]
    source = question_router.invoke({"question": question})
    if source.datasource == "search":
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return "web_search"
    elif source.datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return "vectorstore"


def decide_to_generate(state):
    """
    Xác định xem có nên tạo câu trả lời hay tạo lại câu hỏi hay không.

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        str: Quyết định nhị phân cho nút tiếp theo cần gọi
    """

    print("---ASSESS GRADED DOCUMENTS---")
    state["question"]
    filtered_documents = state["documents"]

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state):
    """
    Xác định xem phần sinh ra có dựa trên tài liệu và trả lời câu hỏi hay không.

    Tham số:
        state (dict): Trạng thái hiện tại của đồ thị

    Trả về:
        str: Quyết định nút tiếp theo cần gọi

    """
    state["retry_count"] = state.get("retry_count", 0) + 1
    if state["retry_count"] > 4:
        print("---DECISION: QUÁ SỐ LẦN THỬ, CHUYỂN SANG TÌM KIẾM TRÊN WEB---")
        state["route"] = "reach_limit"
        return "reach_limit"

    print("---CHECK HALLUCINATIONS---")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]


    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = score.binary_score

    # Check hallucination
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        # Check question-answering
        print("---GRADE GENERATION vs QUESTION---")
        score = answer_grader.invoke({"question": question, "generation": generation})
        grade = score.binary_score
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"

def final_answer(state):
    docs = state["documents"]
    sources = ["Internet"]
    if isinstance(docs, list):
        sources = docs[0].metadata['source']
    if not isinstance(sources, list):
        sources = list(sources)
    if "history" not in state:
        state["history"] = []
    state['history'].append((state['question'], state['generation'], sources))
def not_found_node(state):
    print("Không tìm thấy thông tin.")
    return state

from langgraph.graph import END, StateGraph, START

workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("web_search", web_search)  # web search
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("grade_documents", grade_documents)  # grade documents
workflow.add_node("generate", generate)  # generate
workflow.add_node("transform_query", transform_query)  # transform_query
workflow.add_node("web_generate", web_generate)
workflow.add_node("final_answer", final_answer)

# Build graph
workflow.add_conditional_edges(
    START,
    route_question,
    {
        "web_search": "web_search",
        "vectorstore": "retrieve",
    },
)
workflow.add_edge("web_search", "web_generate")
workflow.add_edge("web_generate", "final_answer")
workflow.add_edge("final_answer", END)
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
workflow.add_conditional_edges(
    "transform_query",
    lambda state: state.get("route", "default"),
    {
        "reach_limit": "web_search",
        "default": "retrieve"
    },
)
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",
        "useful": "final_answer",
        "not useful": "transform_query",
        "reach_limit": "web_search"
    },
)

# Compile
adaptive_rag_graph = workflow.compile()

if __name__ == "__main__":
    # Run
    inputs = {"question": "ĐIỀU CHỈNH DỰ TOÁN CHI NG`ÂN SÁCH NHÀ NƯỚC NĂM 2025"}

    output = adaptive_rag_graph.invoke(inputs)
    question = output["question"]
    result = output["generation"]
    docs= output["documents"]
    source = "Internet"
    if isinstance(docs, list):
        source = docs[0].metadata['source']
    print(question)
    print("-----------------------")
    print(result)
    print("-----------------------")
    print(source)