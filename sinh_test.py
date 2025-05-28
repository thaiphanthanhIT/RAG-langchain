import os
import random
import json
from langchain_community.llms import CTransformers
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# --- Load model local .gguf với CTransformers ---
model_file = "vinallama-2.7b-chat_q5_0.gguf"
llm = CTransformers(
    model=model_file,
    model_type="llama",
    max_new_tokens=1024,
    temperature=0.01
)

# --- Tạo prompt template ---
template = """<|im_start|>system
Bạn là một trợ lí AI hữu ích. Hãy tạo ra một câu hỏi liên quan đến nội dung sau.
<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant"""

prompt = PromptTemplate(template=template, input_variables=["question"])
llm_chain = LLMChain(prompt=prompt, llm=llm)

# --- Đọc file ---
def get_first_n_txt_files(folder, n=100):
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".txt")]
    files.sort()
    return files[:n]

def read_files(files):
    return [open(f, encoding="utf-8").read() for f in files]

# --- Hàm gọi model sinh câu hỏi ---
def generate_question(text):
    input_text = text.strip()[100:500]  # giới hạn input tránh dài quá
    result = llm_chain.invoke({"question": input_text})
    print("LLM result:", result)
    output_text = list(result.values())[0]  # lấy giá trị đầu tiên trong dict
    return output_text.strip()

# --- Task 1: 10 docs ngẫu nhiên ---
def task_1(docs):
    selected = random.sample(docs, 10)
    results = []
    for doc in selected:
        q = generate_question(doc)
        results.append({"doc": doc[:500], "question": q})
    with open("task1_10_questions.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Task 1 done")

# --- Task 2: 20 docs thành 10 cặp ---
def task_2(docs):
    selected = random.sample(docs, 20)
    random.shuffle(selected)
    pairs = [(selected[i], selected[i+1]) for i in range(0, 20, 2)]
    results = []
    for doc1, doc2 in pairs:
        merged = doc1 + "\n\n" + doc2
        q = generate_question(merged)
        results.append({"doc_pair": [doc1[:300], doc2[:300]], "question": q})
    with open("task2_pair_questions.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Task 2 done")

# --- Task 3: 30 docs thành 10 nhóm 3 doc ---
def task_3(docs):
    selected = random.sample(docs, 30)
    random.shuffle(selected)
    triplets = [selected[i:i+3] for i in range(0, 30, 3)]
    results = []
    for triplet in triplets:
        merged = "\n\n".join(triplet)
        q = generate_question(merged)
        results.append({"doc_triplet": [d[:300] for d in triplet], "question": q})
    with open("task3_triplet_questions.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Task 3 done")

# --- Main ---
def main():
    folder_path = r"F:\TinHoc\BinningMini\RAG + langchain\RAG-langchain\crawl\data\tvpl_new\docs"
    files = get_first_n_txt_files(folder_path, 100)
    docs = read_files(files)

    task_1(docs)
    task_2(docs)
    task_3(docs)

if __name__ == "__main__":
    main()
