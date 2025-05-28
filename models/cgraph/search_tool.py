from config import set_environment_variables

set_environment_variables("evaluators")
from langchain_community.tools.tavily_search import TavilySearchResults
web_search_tool = TavilySearchResults()

# from langchain_community.tools import DuckDuckGoSearchRun

# web_search_tool = DuckDuckGoSearchRun()

# search.invoke("Obama's first name?")