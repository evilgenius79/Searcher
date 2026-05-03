import os

import requests


def search_courtlistener(query: str, max_results: int = 10) -> list[dict]:
    """Search US court opinions via CourtListener.

    CourtListener now requires a (free) account token for API reads. If
    COURTLISTENER_TOKEN is set in the environment we use it; otherwise we
    skip the source rather than waste a guaranteed-403 request. Sign up at
    https://www.courtlistener.com to get one.
    """
    token = os.environ.get("COURTLISTENER_TOKEN", "").strip()
    if not token:
        return []
    try:
        r = requests.get(
            "https://www.courtlistener.com/api/rest/v4/search/",
            params={"q": query, "type": "o"},
            headers={"Authorization": f"Token {token}"},
            timeout=12,
        )
        if r.status_code != 200:
            return []
        results = r.json().get("results", [])[:max_results]
        return [
            {
                "case_name": x.get("caseName", ""),
                "court": x.get("court", ""),
                "date": x.get("dateFiled", ""),
                "url": "https://www.courtlistener.com" + (x.get("absolute_url") or ""),
                "snippet": (x.get("snippet", "") or "")[:300],
                "judge": x.get("judge", ""),
            }
            for x in results
        ]
    except Exception:
        return []
