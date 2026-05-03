import wikipediaapi


def search_wikipedia(name: str) -> dict:
    try:
        wiki = wikipediaapi.Wikipedia(
            user_agent="ResearchTool/1.0 (osint-research@tool.local)",
            language="en",
        )
        page = wiki.page(name)
        if page.exists():
            return {
                "title": page.title,
                "summary": page.summary[:3000],
                "url": page.fullurl,
                "sections": [s.title for s in page.sections[:10]],
            }
    except Exception:
        pass
    return {}
