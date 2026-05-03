import requests


def search_hn(query: str, max_results: int = 10) -> list[dict]:
    """Search Hacker News stories via the Algolia public API."""
    try:
        r = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": query,
                "tags": "story",
                "hitsPerPage": str(max_results),
            },
            timeout=10,
        )
        if r.status_code != 200:
            return []
        hits = r.json().get("hits", [])
        results = []
        for h in hits:
            object_id = h.get("objectID", "")
            results.append({
                "title": h.get("title") or h.get("story_title") or "",
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
                "hn_url": f"https://news.ycombinator.com/item?id={object_id}",
                "points": h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "date": (h.get("created_at") or "")[:10],
                "author": h.get("author", ""),
            })
        return results
    except Exception:
        return []
