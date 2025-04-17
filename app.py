import streamlit as st
import logging
from typing import TypedDict, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Attempt to import the compiled app and state from the backend
try:
    from qabot import app as compiled_app, QAState
    BACKEND_AVAILABLE = compiled_app is not None
except ImportError as e:
    logger.error(f"Failed to import backend 'qabot': {e}", exc_info=True)
    st.error("Lỗi: Không thể kết nối đến hệ thống xử lý. Vui lòng thử lại sau.")
    compiled_app = None
    BACKEND_AVAILABLE = False
    # Define QAState minimally if import fails
    class QAState(TypedDict):
        query: str
        result: Optional[str]
        history: List[Tuple[str, str]]
except Exception as e:
    logger.error(f"General error during backend initialization: {e}", exc_info=True)
    st.error("Lỗi: Hệ thống xử lý gặp sự cố khi khởi tạo. Vui lòng thử lại sau.")
    compiled_app = None
    BACKEND_AVAILABLE = False
    class QAState(TypedDict):
        query: str
        result: Optional[str]
        history: List[Tuple[str, str]]

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
    st.caption("Powered by Team 4 - Phạm Văn Thanh, Nguyễn Nam, Phan Thanh Thái, Phạm Công Chiến")

# Main UI
st.title("🤖 Chatbot AI - Bộ Tài Chính")
st.caption("Trợ lý ảo hỗ trợ giải đáp các thắc mắc về quy định tài chính hoặc thông tin chung.")

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
                initial_state = QAState(query=prompt.strip(), result=None, history=history[-3:])  # Chỉ lấy 3 lượt gần nhất để tránh vượt giới hạn
                logger.info(f"Processing query: {prompt} with history: {history}")

                # Invoke backend
                final_state = compiled_app.invoke(initial_state)

                # Process response
                response_content = final_state.get("result", "Không nhận được phản hồi hợp lệ.")
                if not final_state.get("result"):
                    logger.warning(f"No valid result for query: {prompt}")
                    message_placeholder.warning(response_content)
                else:
                    logger.info(f"Response generated: {response_content[:100]}...")
                    message_placeholder.markdown(response_content)

            except Exception as e:
                logger.error(f"Error during query processing: {e}", exc_info=True)
                response_content = f"❌ Đã xảy ra lỗi: {e}. Vui lòng thử lại."
                message_placeholder.error(response_content)

            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": response_content})