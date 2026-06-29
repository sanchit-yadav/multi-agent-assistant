from tavily import TavilyClient
from core.config import TAVILY_API_KEY

_client = TavilyClient(api_key=TAVILY_API_KEY)


def search(query: str, max_results: int = 5) -> list:
    try:
        results = _client.search(query=query, max_results=max_results)
        return [
            {
                "title":   r.get("title", ""),
                "url":     r.get("url", ""),
                "content": r.get("content", ""),
            }
            for r in results.get("results", [])
        ]
    except Exception as e:
        print(f"[Search error] {e}")
        return []
