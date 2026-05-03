import time
from typing import Any

from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    try:
        results = DDGS().text(query, max_results=max_results)
        return list(results) if results else []
    except Exception:
        return []


def search_news(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    try:
        results = DDGS().news(query, max_results=max_results)
        return list(results) if results else []
    except Exception:
        return []
