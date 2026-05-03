import os
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from .report import print_data_summary, save_report
from .research import ResearchEngine
from .synthesis import synthesize_research

console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("target")
@click.option(
    "--type", "-t", "target_type",
    type=click.Choice(["person", "business", "auto"]),
    default="auto",
    show_default=True,
    help="Type of target to research.",
)
@click.option(
    "--depth", "-d",
    type=click.Choice(["quick", "standard", "deep"]),
    default="standard",
    show_default=True,
    help="Research depth (affects number of queries).",
)
@click.option(
    "--domain",
    default="",
    help="Explicit domain for WHOIS lookup (business targets only).",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Save the AI report to a file (.md or .txt).",
)
@click.option(
    "--no-ai", is_flag=True,
    help="Skip AI synthesis; show only gathered data summary.",
)
def cli(target: str, target_type: str, depth: str, domain: str, output: str, no_ai: bool) -> None:
    """Deep-research a person or business using public sources.

    TARGET is the name of the person or organization to research.

    Examples:\n
        python main.py "Elon Musk"\n
        python main.py "OpenAI" --type business\n
        python main.py "Jane Smith" --depth deep --output report.md
    """
    _print_banner()

    # ------------------------------------------------------------------ #
    #  Check API key early so errors are clear                            #
    # ------------------------------------------------------------------ #
    if not no_ai and not os.environ.get("ANTHROPIC_API_KEY"):
        console.print(
            "[red bold]ANTHROPIC_API_KEY is not set.[/red bold]\n"
            "Export it before running:\n"
            "  [cyan]export ANTHROPIC_API_KEY=sk-ant-...[/cyan]\n\n"
            "Or skip AI synthesis with [bold]--no-ai[/bold]."
        )
        sys.exit(1)

    # ------------------------------------------------------------------ #
    #  Build research engine + run                                        #
    # ------------------------------------------------------------------ #
    engine = ResearchEngine(target, target_type, depth, domain)

    console.print(f"[bold]Target :[/bold] {target}")
    console.print(f"[bold]Type   :[/bold] {engine.target_type.title()}")
    console.print(f"[bold]Depth  :[/bold] {depth.title()}")
    if engine.domain and engine.target_type == "business":
        console.print(f"[bold]Domain :[/bold] {engine.domain}")
    console.print()

    data = engine.run(console)

    console.print()
    print_data_summary(data, console)

    if no_ai:
        _print_raw_findings(data)
        return

    # ------------------------------------------------------------------ #
    #  AI synthesis (streaming)                                           #
    # ------------------------------------------------------------------ #
    console.print()
    console.rule("[bold blue]AI Research Report[/bold blue]")
    console.print(
        "[dim]Generating report with Claude claude-opus-4-7 (adaptive thinking)...[/dim]\n"
    )

    report_chunks: list[str] = []
    for chunk in synthesize_research(data):
        console.print(chunk, end="", markup=False, highlight=False)
        report_chunks.append(chunk)

    console.print()  # final newline after streaming

    report_text = "".join(report_chunks)

    if output and report_text:
        save_report(output, target, report_text, console)


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _print_banner() -> None:
    console.print(
        Panel.fit(
            "[bold blue]Online Research Tool[/bold blue]\n"
            "[dim]OSINT research from public sources + Claude AI synthesis[/dim]\n"
            "[dim]Uses only publicly available information.[/dim]",
            border_style="blue",
            padding=(0, 2),
        )
    )
    console.print()


def _print_raw_findings(data: dict) -> None:
    console.print()
    console.rule("[bold]Raw Findings[/bold]")

    if data.get("wikipedia"):
        w = data["wikipedia"]
        console.print(f"\n[bold cyan]Wikipedia:[/bold cyan] {w.get('title', '')}")
        console.print(w.get("summary", "")[:500])

    if data.get("web_results"):
        console.print("\n[bold cyan]Top Web Results:[/bold cyan]")
        for r in data["web_results"][:5]:
            console.print(f"  • [link={r.get('href', '')}]{r.get('title', '')}[/link]")
            console.print(f"    [dim]{r.get('body', '')[:120]}[/dim]")

    if data.get("news"):
        console.print("\n[bold cyan]Recent News:[/bold cyan]")
        for n in data["news"][:5]:
            console.print(
                f"  • {n.get('date', '')} — {n.get('title', '')} "
                f"[dim]({n.get('source', '')})[/dim]"
            )
