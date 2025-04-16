import logging
import os
from typing import TypedDict, Literal, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import FAISS
from duckduckgo_search import DDGS
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Load environment
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("API key GOOGLE_API_KEY chưa được thiết lập trong môi trường hoặc file .env.")

genai.configure(api_key=api_key)

# Khởi tạo models
try:
    routing_model = genai.GenerativeModel("models/gemini-1.5-flash") 
    answering_model = genai.GenerativeModel("models/gemini-1.5-flash") 
    logger.info("Đã khởi tạo thành công model Gemini.")
except Exception as e:
    logger.error(f"Lỗi khởi tạo model Gemini: {e}")
    raise

# Định nghĩa trạng thái LangGraph
class QAState(TypedDict):
    query: str
    # source: Literal["ministry", "search"] # Có thể bỏ source nếu route quyết định trực tiếp node chạy
    result: str | None # Cho phép None để xử lý lỗi


# Tool: Truy vấn dữ liệu Bộ Tài chính (FAISS)
def search_ministry(state: QAState) -> Dict[str, Any]:
    logger.info(">>> Running Tool: search_ministry (FAISS)")
    query = state.get("query")
    if not query:
         logger.error("search_ministry: No query found in state.")
         return {"result": "Lỗi: Không tìm thấy câu hỏi trong state."}

    try:
        # Giả sử embedding model và DB đã tồn tại và đúng đường dẫn
        embedding_model = GPT4AllEmbeddings(model_file="./all-MiniLM-L6-v2-f16.gguf")
        db = FAISS.load_local("vectorstores/db_text", embedding_model, allow_dangerous_deserialization=True)
        logger.info(f"Searching FAISS for: {query}")
        docs = db.similarity_search(query, k=3)
        context = "\n".join([doc.page_content for doc in docs])

        if not context.strip():
             logger.warning("search_ministry: No relevant documents found in FAISS.")
             return {"result": "Không tìm thấy tài liệu liên quan trong cơ sở dữ liệu Bộ Tài chính."}

        prompt = f"""Sử dụng CHỈ thông tin trong ngữ cảnh sau đây để trả lời câu hỏi. Không dùng kiến thức bên ngoài.
Ngữ cảnh:
---
{context}
---
Câu hỏi: {query}

Trả lời:"""
        logger.info(f"[search_ministry] Prompting Gemini...")
        # logger.debug(f"[search_ministry] Full Prompt:\n{prompt}") # Uncomment if needed

        response = answering_model.generate_content(prompt)

        # *** LOGGING CHI TIẾT PHẢN HỒI GEMINI ***
        logger.info(f"[search_ministry] Raw Gemini Response Text: '{response.text}'")
        try:
            logger.info(f"[search_ministry] Gemini Prompt Feedback: {response.prompt_feedback}")
            # logger.info(f"[search_ministry] Gemini Response Parts: {response.parts}") # Uncomment if needed
        except Exception as log_e:
            logger.warning(f"[search_ministry] Cannot log detailed response info: {log_e}")
        # ******************************************

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

# Tool: Tìm kiếm DuckDuckGo
def search_web(state: QAState) -> Dict[str, Any]:
    logger.info(">>> Running Tool: search_web (DuckDuckGo)")
    query = state.get("query")
    if not query:
         logger.error("search_web: No query found in state.")
         return {"result": "Lỗi: Không tìm thấy câu hỏi trong state."}

    try:
        logger.info(f"Searching Web (DDGS) for: {query}")
        with DDGS() as ddgs:
            # Giảm số lượng kết quả để prompt ngắn gọn hơn, tránh vượt giới hạn
            results = list(ddgs.text(query, max_results=3)) # Giảm xuống 3 kết quả

        if not results:
            logger.warning("search_web: No results found on DuckDuckGo.")
            return {"result": "Không tìm thấy thông tin liên quan trên web."}

        context = "\n".join([
            f"Tiêu đề: {r.get('title', '')}\nNội dung: {r.get('body', '')}\nNguồn: {r.get('href', '')}\n---"
            for r in results if r.get('body') # Chỉ lấy kết quả có nội dung
        ]).strip()

        if not context:
            logger.warning("search_web: No content found in DDGS results.")
            return {"result": "Không tìm thấy nội dung cụ thể từ kết quả tìm kiếm web."}

        # Prompt yêu cầu LLM trả lời DỰA TRÊN kết quả tìm kiếm
        prompt = f"""Dựa CHỦ YẾU vào các kết quả tìm kiếm sau đây để trả lời câu hỏi một cách ngắn gọn và chính xác. Trích dẫn nguồn nếu có thể.
Kết quả tìm kiếm:
---
{context}
---
Câu hỏi: {query}

Trả lời:"""
        logger.info(f"[search_web] Prompting Gemini...")
        # logger.debug(f"[search_web] Full Prompt:\n{prompt}") # Uncomment if needed

        response = answering_model.generate_content(prompt)

        # *** LOGGING CHI TIẾT PHẢN HỒI GEMINI ***
        logger.info(f"[search_web] Raw Gemini Response Text: '{response.text}'")
        try:
            logger.info(f"[search_web] Gemini Prompt Feedback: {response.prompt_feedback}")
            # logger.info(f"[search_web] Gemini Response Parts: {response.parts}") # Uncomment if needed
        except Exception as log_e:
            logger.warning(f"[search_web] Cannot log detailed response info: {log_e}")
        # ******************************************

        final_result = response.text.strip()
        if not final_result:
             logger.warning("[search_web] Gemini returned empty or whitespace response.")
             return {"result": "Xin lỗi, tôi không thể tạo câu trả lời từ thông tin tìm kiếm được trên web."}

        return {"result": final_result}

    except Exception as e:
        logger.error(f"Lỗi trong search_web: {e}")
        return {"result": "Đã xảy ra lỗi khi tìm kiếm trên web hoặc xử lý kết quả."}


# Node định tuyến (chọn source)
def route(state: QAState) -> Literal["ministry", "search", "__error__"]:
    logger.info(">>> Running Router Node...")
    query = state.get("query")
    if not query:
        logger.error("Router: No query found in state.")
        # Trả về một trạng thái lỗi hoặc mặc định
        return "__error__" # Hoặc "search" nếu muốn mặc định

    # Prompt rõ ràng hơn, yêu cầu output cụ thể
    routing_prompt = f"""Câu hỏi sau đây liên quan đến lĩnh vực nào?
    1. Thông tin chung cần tìm trên web ('search')
    2. Thông tin chuyên sâu về Bộ Tài chính Việt Nam, văn bản, quy định ('ministry')

    Câu hỏi: "{query}"

    Trả lời CHÍNH XÁC bằng một trong hai từ: 'search' hoặc 'ministry'.
    """
    logger.info("Router: Asking routing_model...")
    try:
        response = routing_model.generate_content(routing_prompt)
        choice = response.text.strip().lower()
        logger.info(f"Router: LLM raw response: '{choice}'")

        # Kiểm tra chặt chẽ hơn
        if "ministry" in choice:
            logger.info("Router: Decision -> ministry")
            return "ministry"
        elif "search" in choice:
            logger.info("Router: Decision -> search")
            return "search"
        else:
            logger.warning(f"Router: Could not determine route from response '{choice}'. Defaulting to 'search'.")
            return "search" # Mặc định tìm kiếm web nếu không rõ

    except Exception as e:
        logger.error(f"Router: Error during routing API call: {e}")
        logger.warning("Router: Error occurred. Defaulting to 'search'.")
        return "search" # Mặc định tìm kiếm web khi có lỗi

# LangGraph Graph setup
workflow = StateGraph(QAState)

# Sửa lại lambda để cập nhật state đúng cách
workflow.add_node("ministry", lambda s: {**s, **search_ministry(s)})
workflow.add_node("search", lambda s: {**s, **search_web(s)})

# Thêm một node xử lý lỗi routing (tùy chọn)
workflow.add_node("handle_error", lambda s: {**s, "result": "Xin lỗi, tôi không thể phân loại câu hỏi của bạn."})


# Entry point là node định tuyến
# Sử dụng hàm route đã định nghĩa ở trên
workflow.set_conditional_entry_point(
    route,
    {
        "ministry": "ministry",
        "search": "search",
        "__error__": "handle_error", # Nếu route trả về lỗi    
    }
)

# Các node đều kết thúc workflow sau khi chạy
workflow.add_edge("ministry", "__end__")
workflow.add_edge("search", "__end__")
workflow.add_edge("handle_error", "__end__") # Node lỗi cũng kết thúc

# Biên dịch graph
try:
    app = workflow.compile()
    logger.info("LangGraph compiled successfully.")
except Exception as e:
     logger.error(f"Error compiling LangGraph: {e}")
     raise

# ---------------------------
# Run Q&A bot
# ---------------------------
if __name__ == "__main__":
    logger.info("Starting Q&A Bot...")
    while True:
        try:
            question = input("❓ Hãy nhập câu hỏi của bạn (hoặc gõ 'quit' để thoát): ")
            if question.lower() == 'quit':
                break
            if not question.strip():
                print("Vui lòng nhập câu hỏi.")
                continue

            initial_state: QAState = {"query": question, "result": None} # Khởi tạo state
            logger.info(f"Invoking graph with query: '{question}'")

            # Chạy graph
            final_state = app.invoke(initial_state)
            logger.info(f"Graph execution finished. Final state: {final_state}")

            # In kết quả
            print("-" * 20)
            answer = final_state.get('result', 'Không có câu trả lời cuối cùng.') # Lấy kết quả từ state
            print(f"📍 Trả lời: {answer}")
            print("-" * 20 + "\n")

        except Exception as e:
            # Ghi log lỗi chi tiết hơn
            logger.exception("An error occurred during the main execution loop:")
            print(f"\n💥 Đã có lỗi xảy ra: {e}")

    logger.info("Q&A Bot stopped.")