import streamlit as st
from qabot import app, QAState  # Import workflow và QAState từ file qabot.py

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="Chatbot AI - Bộ Tài Chính", layout="centered")

# Tiêu đề ứng dụng
st.title("🤖 Chatbot AI - Bộ Tài Chính")
st.write("Hỏi đáp thông tin từ Bộ Tài Chính hoặc tìm kiếm trên web.")

# Lưu trữ lịch sử câu hỏi và trả lời trong session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Hàm hiển thị lịch sử chat
def display_chat_history():
    for entry in st.session_state.history:
        st.chat_message(entry['role']).markdown(entry['message'])

# Hiển thị lịch sử chat
display_chat_history()

# Input câu hỏi từ người dùng
user_input = st.text_input("❓ Nhập câu hỏi của bạn:", placeholder="Ví dụ: Thủ đô của Việt Nam là gì?")

# Nút gửi câu hỏi
if st.button("Gửi câu hỏi"):
    if user_input.strip():
        # Hiển thị trạng thái đang xử lý
        with st.spinner("Đang xử lý câu hỏi..."):
            try:
                # Thêm câu hỏi vào lịch sử chat
                st.session_state.history.append({"role": "user", "message": user_input})

                # Tạo state ban đầu
                initial_state = QAState(query=user_input, result=None)

                # Gọi workflow từ qabot.py
                final_state = app.invoke(initial_state)

                # Lấy kết quả trả lời
                answer = final_state.get("result", "Không có câu trả lời.")
                
                # Thêm câu trả lời vào lịch sử chat
                st.session_state.history.append({"role": "assistant", "message": answer})

                # Hiển thị câu trả lời
                st.success("✅ Trả lời:")
                st.write(answer)
            except Exception as e:
                st.error("❌ Đã xảy ra lỗi khi xử lý câu hỏi.")
                st.write(f"Lỗi chi tiết: {e}")
    else:
        st.warning("⚠️ Vui lòng nhập câu hỏi trước khi gửi.")

# Footer
st.markdown("---")
st.markdown("📌 **Hướng dẫn sử dụng:** Nhập câu hỏi vào ô trên và nhấn nút **Gửi câu hỏi** để nhận câu trả lời.")
