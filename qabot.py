import logging
import os
from typing import TypedDict, Literal, Dict, Any, List, Tuple

import google.generativeai as genai
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import FAISS
from duckduckgo_search import DDGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
VECTOR_DB_PATH = "data/vectorstores/db_text"
MAX_WEB_RESULTS = 5
MODEL_GEMINI = "gemini-1.5-flash"  # Sử dụng model hợp lệ

# Load Gemini API key từ file .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("API key GOOGLE_API_KEY chưa được thiết lập trong môi trường hoặc file .env.")

genai.configure(api_key=api_key)
try:
    routing_model = genai.GenerativeModel(MODEL_GEMINI)
    answering_model = genai.GenerativeModel(MODEL_GEMINI)
    logger.info("Đã khởi tạo thành công model Gemini.")
except Exception as e:
    logger.error(f"Lỗi khởi tạo model Gemini: {e}")
    raise

# Cập nhật QAState để lưu lịch sử trò chuyện
class QAState(TypedDict):
    query: str
    result: str | None
    history: List[Tuple[str, str]]  # Lưu lịch sử dưới dạng [(query, result), ...]

# Tool 1: Truy vấn từ dữ liệu Bộ Tài chính (FAISS)
def search_ministry(state: QAState) -> Dict[str, Any]:
    logger.info(">>> Running Tool: search_ministry (FAISS)")
    query = state.get("query")
    history = state.get("history", [])
    
    if not query:
        logger.error("search_ministry: No query found in state.")
        return {"result": "Lỗi: Không tìm thấy câu hỏi trong state."}

    try:
        embedding_model = GPT4AllEmbeddings(model_file="data/models/all-MiniLM-L6-v2-f16.gguf")
        db = FAISS.load_local(VECTOR_DB_PATH, embedding_model, allow_dangerous_deserialization=True)
        logger.info(f"Searching FAISS for: {query}")
        docs = db.similarity_search(query, k=15)
        context = "\n".join([doc.page_content for doc in docs])

        if not context.strip():
            logger.warning("search_ministry: No relevant documents found in FAISS.")
            return {"result": "Không tìm thấy tài liệu liên quan trong cơ sở dữ liệu Bộ Tài chính."}

        # Thêm lịch sử vào prompt để cung cấp ngữ cảnh
        history_text = "\n".join([f"Người dùng: {q}\nTrợ lý: {r}" for q, r in history[-3:]])  # Chỉ lấy 3 lượt gần nhất để tránh vượt giới hạn token
        prompt = f"""
Bạn là một trợ lý pháp lý thân thiện, am hiểu văn bản pháp luật của Bộ Tài chính.
Trả lời câu hỏi của người dùng CHỈ dựa trên phần "Dữ liệu nội bộ" dưới đây — không suy đoán hay tạo nội dung không có sẵn.

- Nếu không đủ thông tin, hãy nói rõ một cách nhã nhặn (ví dụ: "Dựa theo thông tin tôi có được...").
- Nếu câu hỏi chưa rõ ràng hoặc quá chung chung, hãy khuyến khích người dùng hỏi lại cụ thể hơn.
- Chỉ đề cập đến dữ liệu nội bộ, không nói đến cách cấu trúc hoặc cách bạn nhận được dữ liệu.
- Giải thích gọn, dễ hiểu, và đúng theo nội dung từ Bộ Tài chính, nếu cần hãy trích xuất từ ngữ cảnh được cung cấp cho đầy đủ.
- Nếu không thể xác định câu trả lời từ dữ liệu, hãy nói rõ: "Tôi không tìm thấy thông tin phù hợp trong dữ liệu nội bộ."
- Nếu người dùng yêu cầu chi tiết, hãy trả lời thật chi tiết từ nội dung nội bộ bạn được cung cấp.
- Dựa vào lịch sử trò chuyện để trả lời mạch lạc hơn nếu cần.

Lịch sử trò chuyện:
---
{history_text}
---

Dữ liệu nội bộ:
---
{context}
---

Câu hỏi:
{query}

Trả lời:
Hãy cung cấp một câu trả lời chi tiết, rõ ràng, và đúng theo các dữ liệu trong phần "Dữ liệu nội bộ". Nếu câu trả lời không đầy đủ, xin vui lòng làm rõ thêm với các thông tin mà bạn có được từ dữ liệu.
"""
        logger.info(f"[search_ministry] Prompting Gemini...")
        response = answering_model.generate_content(prompt)
        logger.info(f"[search_ministry] Raw Gemini Response Text: '{response.text}'")
        final_result = response.text.strip()

        if not final_result:
            logger.warning("[search_ministry] Gemini returned empty or whitespace response.")
            return {"result": "Xin lỗi, tôi không thể tạo câu trả lời từ dữ liệu Bộ Tài chính tìm được."}

        return {"result": final_result}

    except FileNotFoundError:
        logger.error("search_ministry: Lỗi không tìm thấy file vectorstores/db_faiss hoặc model embedding.")
        return {"result": "Lỗi: Không thể tải dữ liệu Bộ Tài chính. Vui lòng kiểm tra cài đặt."}
    except Exception as e:
        logger.error(f"Lỗi trong search_ministry: {e}")
        return {"result": "Đã xảy ra lỗi khi truy vấn dữ liệu Bộ Tài chính."}

# Tool 2: Tìm kiếm DuckDuckGo
def search_web(state: QAState) -> Dict[str, Any]:
    logger.info(">>> Running Tool: search_web (DuckDuckGo)")
    query = state.get("query")
    history = state.get("history", [])
    
    if not query:
        logger.error("search_web: No query found in state.")
        return {"result": "Lỗi: Không tìm thấy câu hỏi trong state."}

    try:
        logger.info(f"Searching Web (DDGS) for: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_WEB_RESULTS))

        if not results:
            logger.warning("search_web: No results found on DuckDuckGo.")
            return {"result": "Không tìm thấy thông tin liên quan trên web."}

        context = "\n".join([
            f"Tiêu đề: {r.get('title', '')}\nNội dung: {r.get('body', '')}\nNguồn: {r.get('href', '')}\n---"
            for r in results if r.get('body')
        ]).strip()

        if not context:
            logger.warning("search_web: No content found in DDGS results.")
            return {"result": "Không tìm thấy nội dung cụ thể từ kết quả tìm kiếm web."}

        # Thêm lịch sử vào prompt để cung cấp ngữ cảnh
        history_text = "\n".join([f"Người dùng: {q}\nTrợ lý: {r}" for q, r in history[-3:]])
        prompt = f"""
Dựa CHỦ YẾU vào các kết quả tìm kiếm sau đây để trả lời câu hỏi một cách ngắn gọn và chính xác. Trích dẫn nguồn nếu có thể.
- Dựa vào lịch sử trò chuyện để trả lời mạch lạc hơn nếu cần.
- Nếu không thể xác định câu trả lời từ dữ liệu, hãy nói rõ: "Tôi không tìm thấy thông tin phù hợp trong dữ liệu tìm kiếm trên web."
- Nếu câu hỏi chưa rõ ràng hoặc quá chung chung, hãy khuyến khích người dùng hỏi lại cụ thể hơn.
- Trả lời câu hỏi của người dùng CHỈ dựa trên phần "Kết quả tìm kiếm" dưới đây — không suy đoán hay tạo nội dung không có sẵn.

Lịch sử trò chuyện:
---
{history_text}
---

Kết quả tìm kiếm:
---
{context}
---

Câu hỏi: {query}

Trả lời:
"""
        logger.info(f"[search_web] Prompting Gemini...")
        response = answering_model.generate_content(prompt)
        logger.info(f"[search_web] Raw Gemini Response Text: '{response.text}'")
        final_result = response.text.strip()

        if not final_result:
            logger.warning("[search_web] Gemini returned empty or whitespace response.")
            return {"result": "Xin lỗi, tôi không thể tạo câu trả lời từ thông tin tìm kiếm được trên web."}

        return {"result": final_result}

    except Exception as e:
        logger.error(f"Lỗi trong search_web: {e}")
        return {"result": "Đã xảy ra lỗi khi tìm kiếm trên web hoặc xử lý kết quả."}

# Node định tuyến
def route(state: QAState) -> Literal["ministry", "search", "__error__"]:
    logger.info(">>> Running Router Node...")
    query = state.get("query")
    history = state.get("history", [])
    
    if not query:
        logger.error("Router: No query found in state.")
        return "__error__"

    # Thêm lịch sử vào prompt định tuyến để quyết định chính xác hơn
    history_text = "\n".join([f"Người dùng: {q}\nTrợ lý: {r}" for q, r in history[-3:]])
    routing_prompt = f"""
Câu hỏi sau đây liên quan đến lĩnh vực nào?
1. Thông tin chung cần tìm trên web ('search')
2. Thông tin chuyên sâu về Bộ Tài chính Việt Nam, văn bản, quy định ('ministry')

Lịch sử trò chuyện (nếu có):
---
{history_text}
---

Câu hỏi: "{query}"

Trả lời CHÍNH XÁC bằng một trong hai từ: 'search' hoặc 'ministry'.
"""
    logger.info("Router: Asking routing_model...")
    try:
        response = routing_model.generate_content(routing_prompt)
        choice = response.text.strip().lower()
        logger.info(f"Router: LLM raw response: '{choice}'")

        if "ministry" in choice:
            logger.info("Router: Decision -> ministry")
            return "ministry"
        elif "search" in choice:
            logger.info("Router: Decision -> search")
            return "search"
        else:
            logger.warning(f"Router: Could not determine route from response '{choice}'. Defaulting to 'search'.")
            return "search"

    except Exception as e:
        logger.error(f"Router: Error during routing API call: {e}")
        logger.warning("Router: Error occurred. Defaulting to 'search'.")
        return "search"

# LangGraph Graph setup
workflow = StateGraph(QAState)

# Cập nhật state để bao gồm lịch sử
def update_state_with_history(state: QAState, new_result: Dict[str, Any]) -> QAState:
    current_history = state.get("history", [])
    new_history = current_history + [(state["query"], new_result["result"])]
    return {**state, **new_result, "history": new_history}

workflow.add_node("ministry", lambda s: update_state_with_history(s, search_ministry(s)))
workflow.add_node("search", lambda s: update_state_with_history(s, search_web(s)))
workflow.add_node("handle_error", lambda s: update_state_with_history(s, {"result": "Xin lỗi, tôi không thể phân loại câu hỏi của bạn."}))

workflow.set_conditional_entry_point(
    route,
    {
        "ministry": "ministry",
        "search": "search",
        "__error__": "handle_error",
    }
)

workflow.add_edge("ministry", "__end__")
workflow.add_edge("search", "__end__")
workflow.add_edge("handle_error", "__end__")

# Biên dịch graph
try:
    app = workflow.compile()
    logger.info("LangGraph compiled successfully.")
except Exception as e:
    logger.error(f"Error compiling LangGraph: {e}")
    raise

# Run Q&A bot với lịch sử
if __name__ == "__main__":
    logger.info("Starting Q&A Bot...")
    conversation_history: List[Tuple[str, str]] = []  # Lưu lịch sử toàn bộ cuộc trò chuyện
    state: QAState = {"query": "", "result": None, "history": []}  # Trạng thái ban đầu

    while True:
        try:
            question = input("❓ Hãy nhập câu hỏi của bạn (hoặc gõ 'quit' để thoát): ")
            if question.lower() == 'quit':
                break
            if not question.strip():
                print("Vui lòng nhập câu hỏi.")
                continue

            # Cập nhật trạng thái với câu hỏi mới
            state = {**state, "query": question, "history": conversation_history}
            logger.info(f"Invoking graph with query: '{question}'")

            # Chạy graph
            final_state = app.invoke(state)
            logger.info(f"Graph execution finished. Final state: {final_state}")

            # Cập nhật lịch sử trò chuyện
            result = final_state.get('result', 'Không có câu trả lời cuối cùng.')
            conversation_history.append((question, result))
            state = final_state  # Cập nhật trạng thái cho lần lặp tiếp theo

            # In kết quả
            print("-" * 20)
            print(f"📍 Trả lời: {result}")
            print("-" * 20 + "\n")

        except Exception as e:
            logger.exception("An error occurred during the main execution loop:")
            print(f"\n💥 Đã có lỗi xảy ra: {e}")

    logger.info("Q&A Bot stopped.")