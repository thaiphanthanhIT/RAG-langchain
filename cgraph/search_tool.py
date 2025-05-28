from langchain_community.tools.tavily_search import TavilySearchResults

web_search_tool = TavilySearchResults(k=5)

# Test
query = "Thông tin nóng nhất hôm nay về tài chính Việt Nam"
results = web_search_tool.run(query)

# In kết quả
print("Kết quả tìm kiếm:\n")
for i, result in enumerate(results):
    print(f"[{i+1}] {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Snippet: {result['content']}\n")
