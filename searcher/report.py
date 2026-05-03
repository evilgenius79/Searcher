from rich.console import Console
from rich.table import Table


def print_data_summary(data: dict, console: Console) -> None:
    table = Table(title="Research Data Collected", show_header=True, header_style="bold cyan")
    table.add_column("Source", style="cyan", min_width=24)
    table.add_column("Results", justify="right", style="bold green")

    web_count = len(data.get("web_results", []))
    news_count = len(data.get("news", []))
    wiki_hit = bool(data.get("wikipedia"))
    social_count = len(data.get("social_media", []))
    whois_hit = bool(
        data.get("whois") and any(
            v for v in data["whois"].values() if v and v != "None"
        )
    )

    table.add_row("Web search results", str(web_count))
    table.add_row("News articles", str(news_count))
    table.add_row("Wikipedia entry", "Found" if wiki_hit else "Not found")

    if data.get("type") == "person":
        table.add_row("Professional/social profiles", str(social_count))

    if data.get("type") == "business":
        domain = data.get("domain", "")
        label = f"WHOIS ({domain})" if domain else "WHOIS"
        table.add_row(label, "Found" if whois_hit else "Not found")

    console.print(table)


def save_report(path: str, target: str, report_text: str, console: Console) -> None:
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"# Research Report: {target}\n\n")
            fh.write(report_text)
            fh.write("\n")
        console.print(f"\n[green]Report saved to:[/green] {path}")
    except OSError as exc:
        console.print(f"[red]Could not save report: {exc}[/red]")
