import requests

_USER_AGENT = "ResearchTool/1.0 (+osint research; non-commercial)"


def search_reddit(query: str, max_results: int = 10) -> list[dict]:
    """Search Reddit posts via the public JSON endpoint."""
    try:
        r = requests.get(
            "https://www.reddit.com/search.json",
            params={
                "q": query,
                "limit": str(max_results),
                "sort": "relevance",
                "t": "all",
            },
            headers={"User-Agent": _USER_AGENT},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        children = r.json().get("data", {}).get("children", [])
        results = []
        for c in children[:max_results]:
            d = c.get("data", {})
            results.append({
                "title": d.get("title", ""),
                "subreddit": d.get("subreddit", ""),
                "author": d.get("author", ""),
                "url": "https://reddit.com" + d.get("permalink", ""),
                "score": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "snippet": (d.get("selftext", "") or "")[:300],
            })
        return results
    except Exception:
        return []
