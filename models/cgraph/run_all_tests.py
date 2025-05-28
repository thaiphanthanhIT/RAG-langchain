from grader_doc import retriever, retrieval_grader
from question_rewrite import question_rewriter
from search_tool import web_search_tool
from langchain.schema import Document

# def test_grader_doc():
#     question = "Thông tin chi tiết hướng dẫn chế độ tài chính cho các ngân hàng và tổ chức tài chính tại Việt Nam"
#     docs = retriever.invoke(question)
#     if docs:
#         doc_txt = docs[0].page_content
#         ans = retrieval_grader.invoke({"question": question, "document": doc_txt})
#         print("Có tài liệu liên quan:", ans)
#     else:
#         print("Không có tài liệu liên quan.")

# def test_question_rewrite():
#     question = "Làm thế nào để tối ưu hóa tìm kiếm thông tin tài chính?"
#     result = question_rewriter.invoke({"question": question})
#     print("Câu hỏi sau khi viết lại:", result)

# def test_search_tool():
#     query = "Thông tin nóng nhất hôm nay về tài chính Việt Nam"
#     results = web_search_tool.run(query)
#     print("Kết quả tìm kiếm:\n")
#     for i, result in enumerate(results):
#         print(f"[{i+1}] {result['title']}")
#         print(f"URL: {result['url']}")
#         print(f"Snippet: {result['content']}\n")

def test_with_custom_question():
    question = input("Nhập câu hỏi bất kỳ: ")
    print("\n--- Kết quả chấm điểm tài liệu ---")
    docs = retriever.invoke(question)
    # Lọc tất cả tài liệu liên quan
    relevant_docs = []
    for d in docs:
        ans = retrieval_grader.invoke({"question": question, "document": d.page_content})
        if ans.binary_score.lower() == "có":
            relevant_docs.append(d)
    if relevant_docs:
        print(f"Có {len(relevant_docs)} tài liệu liên quan.")
        from generate import rag_chain
        answer = rag_chain.invoke({"context": relevant_docs, "question": question})
        print("\n--- Câu trả lời chi tiết từ tài liệu ---")
        print(answer)
        return
    else:
        print("Không có tài liệu liên quan.")

    print("\n--- Câu hỏi sau khi viết lại ---")
    result = question_rewriter.invoke({"question": question})
    print(result)

    print("\n--- Kết quả tìm kiếm web ---")
    results = web_search_tool.run(question)
    for i, result in enumerate(results):
        print(f"[{i+1}] {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['content']}\n")

if __name__ == "__main__":
    # print("=== Test grader_doc ===")
    # test_grader_doc()
    # print("\n=== Test question_rewrite ===")
    # test_question_rewrite()
    # print("\n=== Test search_tool ===")
    # test_search_tool()
    print("\n=== Test với câu hỏi bất kỳ ===")
    test_with_custom_question()