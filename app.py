import streamlit as st
import logging
from typing import TypedDict, Optional, List, Tuple
from models.adaptive_rag import *
import streamlit.components.v1 as components
from models.adaptive_rag.main_arag import adaptive_rag_graph as compiled_app, GraphState
from models.manual_query.manual_search import search

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Chatbot AI - Bộ Tài Chính",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for additional information
with st.sidebar:
    st.header("ℹ️ Thông tin")
    st.markdown("""
    - **Chatbot AI** hỗ trợ trả lời các câu hỏi liên quan đến Bộ Tài Chính Việt Nam hoặc tìm kiếm thông tin chung.
    - Dữ liệu được lấy từ cơ sở tri thức nội bộ hoặc tìm kiếm web.
    - Để có kết quả tốt nhất, hãy đặt câu hỏi rõ ràng và cụ thể.
    """)
    st.markdown("---")
    option = st.radio(
        "Lựa chọn chức năng:",
        ["Hỏi đáp chung", "Hỏi đáp theo chuyên ngành", "Tìm kiếm văn bản chính xác"],
        index=0
    )
    if option == "Hỏi đáp theo chuyên ngành":
        chuyen_nganh = st.selectbox(
            "Chọn chuyên ngành:",
            ["Bảo hiểm", "Bất động sản", "Bộ máy hành chính", 
             "Chứng khoán", "Công nghệ thông tin", "Đầu tư", "Dịch vụ pháp lý"]
        )
    st.markdown("---")
    st.caption("Powered by Team 4 - Phạm Văn Thanh, Nguyễn Nam, Phan Thanh Thái, Phạm Công Chiến")

# Attempt to import the compiled app and state from the backend
try:
    if option != "Tìm kiếm văn bản chính xác":
        compiled_app = adaptive_rag_graph
    else:
        compiled_app = search
    BACKEND_AVAILABLE = compiled_app is not None
except ImportError as e:
    logger.error(f"Failed to import backend 'qabot': {e}", exc_info=True)
    st.error("Lỗi: Không thể kết nối đến hệ thống xử lý. Vui lòng thử lại sau.")
    compiled_app = None
    BACKEND_AVAILABLE = False
except Exception as e:
    logger.error(f"General error during backend initialization: {e}", exc_info=True)
    st.error("Lỗi: Hệ thống xử lý gặp sự cố khi khởi tạo. Vui lòng thử lại sau.")
    compiled_app = None
    BACKEND_AVAILABLE = False


# Main UI
st.title("🤖 Chatbot AI - Bộ Tài Chính")
st.caption("Trợ lý ảo hỗ trợ giải đáp các thắc mắc về quy định tài chính hoặc thông tin chung.")
if option == "Tìm kiếm văn bản chính xác":
    st.caption("Bạn đang chọn chế độ tìm kiếm chính xác từ văn bản. Các tính năng khả dụng: Tìm kiếm nội dung văn bản, người ký, ngày ban hành, các văn bản liên quan,...")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! Tôi có thể giúp gì về các quy định tài chính hoặc thông tin khác?"}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input and processing
if prompt := st.chat_input("Nhập câu hỏi của bạn (ví dụ: 'Quy định về thuế TNCN 2023 là gì?')"):
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process if backend is available
    if not BACKEND_AVAILABLE:
        response_content = "Xin lỗi, hệ thống xử lý hiện không khả dụng. Vui lòng thử lại sau."
        with st.chat_message("assistant"):
            st.error(response_content)
        st.session_state.messages.append({"role": "assistant", "content": response_content})
    else:
        # Display processing indicator
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("⚙️ Đang xử lý câu hỏi của bạn...")
            result = ""
            try:
                # Chuẩn bị lịch sử trò chuyện từ st.session_state.messages
                history = []
                for i in range(0, len(st.session_state.messages) - 1):  # Bỏ qua tin nhắn hiện tại (đang xử lý)
                    msg = st.session_state.messages[i]
                    if msg["role"] == "user" and i + 1 < len(st.session_state.messages):
                        next_msg = st.session_state.messages[i + 1]
                        if next_msg["role"] == "assistant":
                            history.append((msg["content"], next_msg["content"]))

                # Initialize state with query and history
                initial_state = GraphState(question=prompt.strip(), generation=None,retry_count=0, history=history[-3:])  # Chỉ lấy 3 lượt gần nhất để tránh vượt giới hạn
                logger.info(f"Processing query: {prompt} with history: {history}")

                # Invoke backend
                final_state = compiled_app.invoke(initial_state)

                # Process response
                result = final_state.get("generation","Không nhận được phản hồi hợp lệ.") 
                docs = final_state["documents"]
                print(type(docs))
                sources = "Internet"
                html_srcs = []
                if isinstance(docs, list):
                    sources = docs[0].metadata['source']
                    print(sources)
                    if not isinstance(sources, list):
                        sources = [sources]
                    for src in sources: 
                        doc_name = src.split('\\')[-1]
                        print(f"doc_name: {doc_name} ")
                        html_name = doc_name.replace('.txt', '.html')
                        html_src = "crawl/data/tvpl_new/html/" + html_name
                        print(html_src)
                        html_srcs.append(html_src)
                print(html_srcs)
                if not final_state.get("generation"):
                    logger.warning(f"No valid result for query: {prompt}")
                    message_placeholder.warning(result)
                else:
                    logger.info(f"Response generated: {result}...")
                    message_placeholder.markdown(result)
                    if len(html_srcs) > 0 : 
                        all_html = ""
                        for src in html_srcs:
                            logger.info(f"source: {src}")
                            with open(src, "r", encoding="utf-8") as f: 
                                all_html += f.read()
                                all_html += "<hr>"  # Thêm đường kẻ giữa các file (tùy chọn)
                        centered_html = f"""
                        <div style="display: flex; justify-content: center;">
                            <div style="width: 600px;">
                                {all_html}
                            </div>
                        </div>
                        """
                        components.html(centered_html,height=1500, width = 900 ,scrolling=True)
                    

            except Exception as e:
                logger.error(f"Error during query processing: {e}", exc_info=True)
                response_content = f"❌ Đã xảy ra lỗi: {e}. Vui lòng thử lại."
                message_placeholder.error(response_content)

            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": result})