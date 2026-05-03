import requests

_USER_AGENT = "ResearchTool/1.0 (+osint research)"


def get_wayback_snapshots(url: str, limit: int = 15) -> list[dict]:
    """Return a sample of Wayback Machine snapshots for the given URL/domain."""
    if not url:
        return []
    try:
        r = requests.get(
            "https://web.archive.org/cdx/search/cdx",
            params={
                "url": url,
                "limit": str(limit),
                "output": "json",
                "fl": "timestamp,original,statuscode,mimetype",
                "filter": "statuscode:200",
                "collapse": "timestamp:6",
            },
            headers={"User-Agent": _USER_AGENT},
            timeout=12,
        )
        if r.status_code != 200:
            return []
        rows = r.json()
        if not rows or len(rows) < 2:
            return []
        return [
            {
                "timestamp": row[0],
                "original_url": row[1],
                "snapshot_url": f"https://web.archive.org/web/{row[0]}/{row[1]}",
            }
            for row in rows[1:]
        ]
    except Exception:
        return []
