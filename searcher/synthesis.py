from typing import Generator

import anthropic

SYNTHESIS_SYSTEM_PROMPT = """\
You are an expert OSINT (Open Source Intelligence) analyst. Your role is to \
analyze publicly available information and produce accurate, well-structured \
research reports.

Guidelines:
- Base your analysis ONLY on the provided data. Never fabricate information.
- Use factual, neutral language throughout.
- When data is sparse or uncertain, say so clearly.
- Highlight notable patterns, connections, or findings.
- Keep sections concise but thorough.

Report structure (include only sections where data exists):

## Overview
Who or what this entity is; key identifying facts.

## Background & History
Origins, founding story, early career, or historical context.

## Professional / Business Profile
Current role, activities, industry, notable work or products.

## Online Presence
Social media, websites, notable digital footprint.

## News & Media Coverage
Recent and significant news mentions.

## Key Connections & Associations
Related organizations, key people, or partnerships.

## Key Findings
The most important takeaways, any notable patterns or red flags.

Use bullet points for lists. When referencing a source type, say so briefly \
(e.g. "News reports indicate…", "Wikipedia notes…").\
"""


def synthesize_research(data: dict) -> Generator[str, None, None]:
    """Yield text chunks of the AI-generated research report (streaming)."""
    try:
        client = anthropic.Anthropic()
        research_text = _format_research_data(data)

        if not research_text.strip():
            yield "No research data was collected — unable to generate report."
            return

        prompt = (
            f'Research Target: "{data["target"]}" '
            f'(Type: {data.get("type", "unknown").title()})\n\n'
            f"{research_text}\n\n"
            "Generate a comprehensive research report based on the data above."
        )

        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYNTHESIS_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    except anthropic.AuthenticationError:
        yield "\n[Error: Invalid ANTHROPIC_API_KEY. Check your environment.]\n"
    except anthropic.APIConnectionError:
        yield "\n[Error: Could not connect to Anthropic API.]\n"
    except anthropic.RateLimitError:
        yield "\n[Error: Anthropic API rate limit reached. Try again shortly.]\n"
    except Exception as exc:
        yield f"\n[Synthesis error: {exc}]\n"


def _format_research_data(data: dict) -> str:
    parts: list[str] = []

    if data.get("web_results"):
        parts.append("=== WEB SEARCH RESULTS ===")
        for r in data["web_results"][:15]:
            parts.append(f"Title: {r.get('title', '')}")
            parts.append(f"URL:   {r.get('href', '')}")
            snippet = r.get("body", "")[:300]
            parts.append(f"Snippet: {snippet}")
            parts.append("")

    if data.get("news"):
        parts.append("=== NEWS RESULTS ===")
        for n in data["news"][:10]:
            parts.append(f"Title:  {n.get('title', '')}")
            parts.append(f"Source: {n.get('source', '')}")
            parts.append(f"Date:   {n.get('date', '')}")
            body = n.get("body", "")[:300]
            parts.append(f"Body:   {body}")
            parts.append("")

    if data.get("wikipedia"):
        w = data["wikipedia"]
        parts.append("=== WIKIPEDIA ===")
        parts.append(f"Title:   {w.get('title', '')}")
        parts.append(f"URL:     {w.get('url', '')}")
        parts.append(f"Summary: {w.get('summary', '')[:2500]}")
        if w.get("sections"):
            parts.append(f"Sections: {', '.join(w['sections'])}")
        parts.append("")

    if data.get("social_media"):
        parts.append("=== PROFESSIONAL / SOCIAL PROFILES ===")
        for r in data["social_media"][:8]:
            parts.append(f"Title:   {r.get('title', '')}")
            parts.append(f"URL:     {r.get('href', '')}")
            parts.append(f"Snippet: {r.get('body', '')[:200]}")
            parts.append("")

    if data.get("whois"):
        whois_data = {
            k: v for k, v in data["whois"].items() if v and v != "None"
        }
        if whois_data:
            parts.append("=== DOMAIN / WHOIS ===")
            if data.get("domain"):
                parts.append(f"Domain: {data['domain']}")
            for k, v in whois_data.items():
                parts.append(f"{k.title().replace('_', ' ')}: {v}")
            parts.append("")

    if data.get("hacker_news"):
        parts.append("=== HACKER NEWS MENTIONS ===")
        for h in data["hacker_news"][:10]:
            parts.append(f"Title:    {h.get('title', '')}")
            parts.append(f"Date:     {h.get('date', '')}")
            parts.append(f"Points:   {h.get('points', 0)}  Comments: {h.get('comments', 0)}")
            parts.append(f"URL:      {h.get('url', '')}")
            parts.append("")

    if data.get("reddit"):
        parts.append("=== REDDIT POSTS ===")
        for p in data["reddit"][:10]:
            parts.append(f"Title:    {p.get('title', '')}")
            parts.append(f"Subreddit: r/{p.get('subreddit', '')}")
            parts.append(f"Score:    {p.get('score', 0)}  Comments: {p.get('comments', 0)}")
            parts.append(f"URL:      {p.get('url', '')}")
            snippet = p.get("snippet", "")
            if snippet:
                parts.append(f"Snippet:  {snippet}")
            parts.append("")

    if data.get("court_records"):
        parts.append("=== COURT RECORDS (CourtListener) ===")
        for c in data["court_records"][:10]:
            parts.append(f"Case:    {c.get('case_name', '')}")
            parts.append(f"Court:   {c.get('court', '')}")
            parts.append(f"Date:    {c.get('date', '')}")
            parts.append(f"URL:     {c.get('url', '')}")
            snippet = c.get("snippet", "")
            if snippet:
                parts.append(f"Snippet: {snippet}")
            parts.append("")

    if data.get("sec_filings"):
        parts.append("=== SEC EDGAR FILINGS ===")
        for f in data["sec_filings"][:10]:
            parts.append(f"Form:     {f.get('form', '')}")
            parts.append(f"Filed:    {f.get('filed', '')}")
            parts.append(f"Filer:    {f.get('company', '')}")
            parts.append(f"Acc. No.: {f.get('accession', '')}")
            if f.get("url"):
                parts.append(f"URL:      {f.get('url', '')}")
            parts.append("")

    gh = data.get("github") or {}
    if gh.get("users") or gh.get("repos"):
        parts.append("=== GITHUB ===")
        for u in gh.get("users", [])[:5]:
            parts.append(
                f"User: {u.get('login', '')} ({u.get('type', '')}) - {u.get('url', '')}"
            )
        for r in gh.get("repos", [])[:5]:
            parts.append(
                f"Repo: {r.get('name', '')} "
                f"[{r.get('language', '') or 'unknown'}, ★{r.get('stars', 0)}] "
                f"- {r.get('description', '')}"
            )
            parts.append(f"      {r.get('url', '')}")
        parts.append("")

    if data.get("wayback"):
        parts.append("=== WAYBACK MACHINE SNAPSHOTS ===")
        snaps = data["wayback"]
        first, last = snaps[0], snaps[-1]
        parts.append(
            f"Earliest snapshot: {first.get('timestamp', '')}  {first.get('snapshot_url', '')}"
        )
        parts.append(
            f"Latest snapshot:   {last.get('timestamp', '')}  {last.get('snapshot_url', '')}"
        )
        parts.append(f"Total snapshots sampled: {len(snaps)}")
        parts.append("")

    return "\n".join(parts)
