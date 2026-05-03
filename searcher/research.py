import re
import time
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .sources.court_listener import search_courtlistener
from .sources.github_search import search_github
from .sources.hacker_news import search_hn
from .sources.reddit import search_reddit
from .sources.sec_edgar import search_edgar
from .sources.wayback import get_wayback_snapshots
from .sources.web_search import search_news, search_web
from .sources.whois_lookup import lookup_domain
from .sources.wikipedia import search_wikipedia

_BUSINESS_KEYWORDS = {
    "inc", "llc", "corp", "ltd", "company", "co.", "group",
    "tech", "solutions", "services", "enterprises", "holdings",
    "associates", "partners", "global", "international", "systems",
}

_DEPTH_RESULT_COUNT = {"quick": 5, "standard": 8, "deep": 15}


class ResearchEngine:
    def __init__(
        self,
        target: str,
        target_type: str = "auto",
        depth: str = "standard",
        domain: str = "",
    ):
        self.target = target
        self.target_type = (
            self._detect_type(target) if target_type == "auto" else target_type
        )
        self.depth = depth
        self.max_results = _DEPTH_RESULT_COUNT.get(depth, 8)
        self.domain = domain or self._guess_domain()

    def _detect_type(self, target: str) -> str:
        lower = target.lower()
        for kw in _BUSINESS_KEYWORDS:
            if kw in lower.split() or lower.endswith(f" {kw}"):
                return "business"
        # Two or more words that look like a name → person
        words = target.strip().split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w):
            return "person"
        return "business"

    def _guess_domain(self) -> str:
        if self.target_type != "business":
            return ""
        name = self.target.lower()
        for suffix in [
            " inc", " llc", " corp", " ltd", " co", " company",
            " group", " tech", " solutions",
        ]:
            name = name.replace(suffix, "")
        name = re.sub(r"[^a-z0-9]", "", name.strip())
        return f"{name}.com" if name else ""

    def run(self, console: Console) -> dict[str, Any]:
        data: dict[str, Any] = {
            "target": self.target,
            "type": self.target_type,
            "web_results": [],
            "news": [],
            "wikipedia": {},
            "social_media": [],
            "whois": {},
            "domain": self.domain,
            "hacker_news": [],
            "reddit": [],
            "court_records": [],
            "sec_filings": [],
            "github": {"users": [], "repos": []},
            "wayback": [],
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            t1 = progress.add_task("Searching the web...", total=None)
            data["web_results"] = self._web_search()
            time.sleep(0.3)
            progress.update(t1, description="[green]Web search done")

            t2 = progress.add_task("Searching news archives...", total=None)
            data["news"] = self._news_search()
            time.sleep(0.3)
            progress.update(t2, description="[green]News search done")

            t3 = progress.add_task("Querying Wikipedia...", total=None)
            data["wikipedia"] = search_wikipedia(self.target)
            progress.update(t3, description="[green]Wikipedia done")

            if self.target_type == "person":
                t4 = progress.add_task(
                    "Searching professional profiles...", total=None
                )
                data["social_media"] = self._social_search()
                progress.update(t4, description="[green]Profile search done")
            else:
                t4 = progress.add_task("Looking up domain info...", total=None)
                if self.domain:
                    data["whois"] = lookup_domain(self.domain)
                progress.update(t4, description="[green]Domain lookup done")

            t5 = progress.add_task("Searching Hacker News...", total=None)
            data["hacker_news"] = search_hn(self.target, self.max_results)
            progress.update(t5, description="[green]Hacker News done")

            t6 = progress.add_task("Searching Reddit...", total=None)
            data["reddit"] = search_reddit(f'"{self.target}"', self.max_results)
            progress.update(t6, description="[green]Reddit done")

            t7 = progress.add_task("Searching court records...", total=None)
            data["court_records"] = search_courtlistener(
                f'"{self.target}"', self.max_results
            )
            progress.update(t7, description="[green]Court records done")

            t8 = progress.add_task("Searching SEC EDGAR...", total=None)
            data["sec_filings"] = search_edgar(self.target, self.max_results)
            progress.update(t8, description="[green]SEC EDGAR done")

            t9 = progress.add_task("Searching GitHub...", total=None)
            data["github"] = search_github(self.target, max_results=5)
            progress.update(t9, description="[green]GitHub done")

            if self.target_type == "business" and self.domain:
                t10 = progress.add_task(
                    "Fetching Wayback Machine snapshots...", total=None
                )
                data["wayback"] = get_wayback_snapshots(self.domain, limit=15)
                progress.update(t10, description="[green]Wayback done")

        return data

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _web_search(self) -> list:
        seen_urls: set = set()
        all_results: list = []
        for query in self._web_queries():
            for r in search_web(query, self.max_results):
                url = r.get("href", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(r)
            time.sleep(0.4)
        return all_results[: self.max_results * 2]

    def _news_search(self) -> list:
        return search_news(f'"{self.target}"', self.max_results)

    def _social_search(self) -> list:
        queries = [
            f'"{self.target}" linkedin profile',
            f'"{self.target}" twitter',
        ]
        results: list = []
        seen: set = set()
        for q in queries:
            for r in search_web(q, 5):
                url = r.get("href", "")
                if url not in seen:
                    seen.add(url)
                    results.append(r)
            time.sleep(0.4)
        return results[:10]

    def _web_queries(self) -> list[str]:
        if self.target_type == "person":
            queries = [
                f'"{self.target}"',
                f'"{self.target}" biography career',
                f'"{self.target}" professional background',
            ]
            if self.depth in ("standard", "deep"):
                queries += [
                    f'"{self.target}" interview achievements',
                    f'"{self.target}" work projects',
                ]
        else:
            queries = [
                f'"{self.target}"',
                f'"{self.target}" company overview about',
                f'"{self.target}" leadership executives founders',
            ]
            if self.depth in ("standard", "deep"):
                queries += [
                    f'"{self.target}" products services revenue',
                    f'"{self.target}" history founding story',
                ]
        return queries
