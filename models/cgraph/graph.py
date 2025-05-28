from typing import List, Tuple
from typing_extensions import TypedDict
from langchain.schema import Document
from langgraph.graph import END, StateGraph, START
from search_tool import web_search_tool
from grader_doc import retrieval_grader, retriever
from question_rewrite import question_rewriter
from generate import rag_chain
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
    try_count: int
    history: List[Tuple[str, str, List[str]]]


def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    documents = retriever.invoke(question)
    if "documents" not in state:
        state["documents"] = []
    state["documents"] = documents
    return state


def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    state["try_count"] = state.get("try_count", 0) + 1
    if state["try_count"] > 5: 
        print("------REACH LIMIT----")
        return state
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    if "documents" not in state:
        state["documents"] = []
    state["documents"] = documents
    if "generation" not in state:
        state["generation"] = ""
    state["generation"] = generation
    return state


def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    filtered_docs = []
    for d in documents:
        id_doc = extract_main_code(d)
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content, "id_document": id_doc}
        )
        print(score)
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
    # Nếu có ít nhất 1 tài liệu liên quan thì trả lời luôn
    has_relevant = len(filtered_docs) > 0
    if "has_relevant" not in state:
        state["has_relevant"] = 0
    state["has_relevant"] = has_relevant
    state["documents"] = filtered_docs
    return state
    #return {"documents": filtered_docs, "question": question, "has_relevant": has_relevant}

def transform_query(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    question = state["question"]

    # Re-write question
    better_question = question_rewriter.invoke({"question": question})
    state["question"] = better_question
    return state
    #return {"documents": documents, "question": better_question}


def web_search(state):
    """
    Web search based on the re-phrased question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """
    state["try_count"] = state.get("try_count", 0) + 1
    if state["try_count"] > 5: 
        print("------REACH LIMIT----")
        state["route"] = "reach_limit"
        return state
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state["documents"]

    # Web search
    docs = web_search_tool.invoke({"query": question})
    if docs and isinstance(docs[0], dict):
        web_results_text = "\n".join([d["content"] for d in docs])
    else:
        web_results_text = "\n".join(docs)

    web_results = Document(page_content=web_results_text)
    documents.append(web_results)
    state["documents"] = documents
    return state
    #return {"documents": documents, "question": question}
def final_answer(state):
    docs = state["documents"]
    sources = ["Internet"]
    if isinstance(docs, list) and len(docs) > 0:
        sources = docs[0].metadata['source']
    if not isinstance(sources, list):
        sources = list(sources)
    if "history" not in state:
        state["history"] = []
    state['history'].append((state['question'], state.get('generation',"Tôi không thể trả lời câu hỏi này"), sources))
    state["generation"] = state.get('generation',"Tôi không thể trả lời câu hỏi này")
    return state

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.
    """

    print("---ASSESS GRADED DOCUMENTS---")
    if state.get("has_relevant", False):
        print("---DECISION: GENERATE---")
        return "generate"
    else:
        print("---DECISION: TRANSFORM QUERY & WEB SEARCH---")
        return "transform_query"


# Build the workflow graph
workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search", web_search)
workflow.add_node("final_answer", final_answer)

workflow.add_edge(START, "retrieve")
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
    "web_search",
    lambda state: state.get("route", "default"),
    {
        "reach_limit": "generate",
        "default": "grade_documents"
    },
)
workflow.add_edge("transform_query", "web_search")
workflow.add_edge("generate", "final_answer")
workflow.add_edge("final_answer", END)

app = workflow.compile()

if __name__ == "__main__":
    inputs = {"question": "ĐIỀU CHỈNH DỰ TOÁN CHI NGÂN SÁCH NHÀ NƯỚC NĂM 2025"}
    for output in app.stream(inputs):
        for k,v in output.items():
            print(f"Node: {k}" )
            #print(f"{v}")
    print(v["generation"])
    print(v["documents"])
    