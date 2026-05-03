import requests

_USER_AGENT = "ResearchTool research-osint@example.com"


def search_edgar(query: str, max_results: int = 10) -> list[dict]:
    """Full-text SEC EDGAR filings search. No API key required (User-Agent is)."""
    try:
        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{query}"'},
            headers={"User-Agent": _USER_AGENT},
            timeout=12,
        )
        if r.status_code != 200:
            return []
        hits = r.json().get("hits", {}).get("hits", [])[:max_results]
        results: list[dict] = []
        for h in hits:
            src = h.get("_source", {})
            cik = (src.get("ciks") or [""])[0]
            form = src.get("form", "")
            url = (
                f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
                if cik else ""
            )
            results.append({
                "form": form,
                "filed": src.get("file_date", ""),
                "company": ", ".join(src.get("display_names", []))[:200],
                "accession": src.get("adsh", ""),
                "url": url,
            })
        return results
    except Exception:
        return []
