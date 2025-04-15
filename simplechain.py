from langchain_community.llms import CTransformers
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms.loading import load_llm

model_files = "vinallama-2.7b-chat_q5_0.gguf"

def load_file(model_file):
    llm = CTransformers(
        model=model_file,
        model_type="llama",
        max_new_tokens=1024,
        temperature=0.01
    )
    return llm

def create_prompt(template):
    prompt = PromptTemplate(template=template, input_variables=["question"])
    return prompt

def create_simple_chain(prompt, llm):
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    return llm_chain

# Template có biến {question}
template = """<|im_start|>system
Bạn là một trợ lí AI hữu ích. Hãy trả lời người dùng một cách chính xác.
<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant"""

prompt = create_prompt(template)
llm = load_file(model_files)  # Dùng hàm load_file, không phải load_llm
llm_chain = create_simple_chain(prompt, llm)

question = "Các món ăn nổi tiếng ở Việt Nam là gì?"
response = llm_chain.invoke({"question": question})
print(response)
