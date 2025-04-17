import logging
import os
from typing import TypedDict, Literal, Dict, Any, List, Tuple

import google.generativeai as genai
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI

from config import set_environment_variables
set_environment_variables("evaluators")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from config import set_environment_variables
set_environment_variables("evaluators")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Tên file mô hình và đường dẫn vector DB
model_file = "vinallama-2.7b-chat_q5_0.gguf"
vector_db_path = "vectorstores/db_text" # faiss -> pdf

# # Load mô hình LLM từ file .gguf
# def load_file(model_file):
#     llm = CTransformers(
#         model=model_file,
#         model_type="llama",
#         max_new_tokens=1024,
#         temperature=0.01
#     )
#     return llm

# Tạo prompt theo template
def create_prompt(template):
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    return prompt

# Tạo Retrieval QA chain
def create_qa_chain(prompt, llm, db):
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 20}
        search_kwargs={"k": 20}
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    return qa_chain

# Load FAISS vector database
def read_vector_db():
    embedding_model = GPT4AllEmbeddings(model_file="all-MiniLM-L6-v2-f16.gguf")
    db = FAISS.load_local(
        vector_db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )
    return db

# Bắt đầu chạy QA bot
if __name__ == "__main__":
    db = read_vector_db()
    # llm = load_file(model_file)
    # llm = load_file(model_file)

    template = """<|im_start|>system
Sử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, hãy nói không biết.
{context}<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant"""

    prompt = create_prompt(template)
    llm_chain = create_qa_chain(prompt, llm, db)

    question = "Hãy trình bày những quy định về cách sắp xếp tổ chức đơn vị dự toán ngân sách nhà nước đối với các Đảng ủy mới thành lập ở Trung ương và địa phương"
    response = llm_chain.invoke({"query": question})

    print("Câu hỏi:", question)
    print("Trả lời:", response['result'])