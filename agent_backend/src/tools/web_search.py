from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults

@tool
def web_search(query: str) -> str:
    """Search the web for information and return relevant results using DuckDuckGo."""
    try:
        search = DuckDuckGoSearchResults(num_results=5)
        return search.run(query)
    except Exception as e:
        return f"Error during web search: {str(e)}"
