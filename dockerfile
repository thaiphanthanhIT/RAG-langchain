# Base image đồng bộ với local version
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép toàn bộ project vào container
COPY . /app

# Cài đặt pip và dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Mở port cho Streamlit
EXPOSE 8501

# Chạy ứng dụng Streamlit
CMD ["streamlit", "run", "app.py"]
