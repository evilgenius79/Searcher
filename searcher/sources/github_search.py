import requests

_USER_AGENT = "ResearchTool/1.0"


def search_github(query: str, max_results: int = 5) -> dict:
    """Search GitHub for users/orgs and repositories matching the target."""
    result: dict = {"users": [], "repos": []}
    try:
        users_resp = requests.get(
            "https://api.github.com/search/users",
            params={"q": query, "per_page": str(max_results)},
            headers={"User-Agent": _USER_AGENT, "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if users_resp.status_code == 200:
            for u in users_resp.json().get("items", [])[:max_results]:
                result["users"].append({
                    "login": u.get("login", ""),
                    "url": u.get("html_url", ""),
                    "type": u.get("type", ""),
                })
    except Exception:
        pass

    try:
        repos_resp = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "per_page": str(max_results), "sort": "stars"},
            headers={"User-Agent": _USER_AGENT, "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if repos_resp.status_code == 200:
            for repo in repos_resp.json().get("items", [])[:max_results]:
                result["repos"].append({
                    "name": repo.get("full_name", ""),
                    "description": (repo.get("description") or "")[:200],
                    "url": repo.get("html_url", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language") or "",
                })
    except Exception:
        pass

    return result
