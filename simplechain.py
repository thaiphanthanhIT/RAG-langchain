import logging
from langchain_community.llms import CTransformers
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_FILE = "./vinallama-2.7b-chat_q5_0.gguf"

def load_file(model_file):
    try:
        logger.info("Đang tải mô hình LLM...")
        llm = CTransformers(
            model=model_file,
            model_type="llama",
            max_new_tokens=1024,
            temperature=0.01
        )
        logger.info("Mô hình LLM đã được tải thành công.")
        return llm
    except Exception as e:
        logger.error(f"Lỗi khi tải mô hình LLM: {e}")
        raise

def create_prompt(template):
    return PromptTemplate(template=template, input_variables=["question"])

def create_simple_chain(prompt, llm):
    return LLMChain(prompt=prompt, llm=llm)

if __name__ == "__main__":
    try:
        template = """<|im_start|>system
Bạn là một trợ lí AI hữu ích. Hãy trả lời người dùng một cách chính xác.
<|im_end|>
<|im_start|>user
{question}<|im_end|>
<|im_start|>assistant"""

        prompt = create_prompt(template)
        llm = load_file(MODEL_FILE)
        llm_chain = create_simple_chain(prompt, llm)

        question = "Các món ăn nổi tiếng ở Việt Nam là gì?"
        response = llm_chain.invoke({"question": question})
        print(response)
    except Exception as e:
        logger.exception("Đã xảy ra lỗi trong quá trình chạy chuỗi đơn giản.")