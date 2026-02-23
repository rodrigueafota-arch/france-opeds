"""
france_debate.py — CLI entry point for the France Op-Ed & Debate Engine.

Commands:
  opeds   — Generate opening op-ed pieces from all (or one) persona(s).
  debate  — Generate op-eds then run multi-round debate with a moderator.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Load .env before importing engine modules (which instantiate the client)
load_dotenv()

# Guard: fail fast with a clean error if the key is missing
if not os.environ.get("ANTHROPIC_API_KEY"):
    console = Console(stderr=True)
    console.print(
        "[bold red]Error:[/bold red] ANTHROPIC_API_KEY is not set.\n"
        "Copy .env.example to .env and add your Anthropic API key.",
        highlight=False,
    )
    sys.exit(1)

from debate_engine import (  # noqa: E402
    generate_debate_response,
    generate_moderator_summary,
    generate_op_ed,
)
from fact_checker import fact_check  # noqa: E402
from personas import ALL_PERSONAS, PERSONAS_BY_ID  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("output")

# Colour map keyed by persona id (matches ARCHITECTURE.md styling table)
PERSONA_COLOURS: dict[str, str] = {
    "le_tribun": "red",
    "le_rationaliste": "cyan",
    "le_pragmatique": "green",
    "le_visionnaire": "magenta",
    "le_patriote": "blue",
    "l_economiste": "yellow",
}

app = typer.Typer(
    name="france-debate",
    help="Simulate six French intellectuals writing op-eds and debating each other.",
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug(text: str) -> str:
    """Convert a topic string into a filesystem-safe slug."""
    import re
    text = text.lower()
    text = re.sub(r"[àáâãäå]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:60]


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _panel_title(persona: dict) -> str:
    return f"{persona['name']} — {persona['tagline']}"


def _display_op_ed(persona: dict, text: str, fact_check_notes: str) -> None:
    colour = PERSONA_COLOURS.get(persona["id"], "white")
    panel = Panel(
        text,
        title=_panel_title(persona),
        border_style=colour,
        padding=(1, 2),
    )
    console.print(panel)
    if fact_check_notes:
        warning = Text(f"⚠ Fact-check notes: {fact_check_notes}", style="orange1")
        console.print(warning)
        console.print()


def _display_debate_response(persona: dict, text: str) -> None:
    colour = PERSONA_COLOURS.get(persona["id"], "white")
    panel = Panel(
        text,
        title=persona["name"],
        border_style=colour,
        padding=(1, 2),
    )
    console.print(panel)


def _display_moderator(text: str, round_number: int) -> None:
    panel = Panel(
        text,
        title=f"🎙 Modérateur — Round {round_number}",
        border_style="bright_yellow",
        padding=(1, 2),
    )
    console.print(panel)


# ---------------------------------------------------------------------------
# Core op-ed generation flow (shared by both commands)
# ---------------------------------------------------------------------------


def _run_opeds(
    topic: str,
    do_fact_check: bool,
    personas: list[dict],
) -> list[dict]:
    """
    Generate op-eds for the given list of personas.

    Returns a list of dicts:
      {"persona": dict, "persona_name": str, "text": str, "fact_check_notes": str}
    """
    results: list[dict] = []

    for persona in personas:
        with console.status(
            f"[bold]{persona['name']}[/bold] is writing...", spinner="dots"
        ):
            try:
                raw_text = generate_op_ed(persona, topic)
            except Exception as exc:
                console.print(
                    f"[bold red]Warning:[/bold red] Failed to generate op-ed for "
                    f"{persona['name']}: {exc}"
                )
                continue

        fact_check_notes = ""
        display_text = raw_text

        if do_fact_check:
            with console.status(
                f"[bold]Fact-checking[/bold] {persona['name']}'s op-ed...", spinner="dots"
            ):
                try:
                    fc_result = fact_check(raw_text, persona["name"])
                    display_text = fc_result["corrected_text"]
                    fact_check_notes = fc_result["fact_check_notes"]
                except Exception as exc:
                    console.print(
                        f"[bold red]Warning:[/bold red] Fact-check failed for "
                        f"{persona['name']}: {exc}"
                    )

        _display_op_ed(persona, display_text, fact_check_notes)
        results.append(
            {
                "persona": persona,
                "persona_name": persona["name"],
                "text": display_text,
                "fact_check_notes": fact_check_notes,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Markdown serialisation
# ---------------------------------------------------------------------------


def _build_opeds_markdown(topic: str, timestamp: str, op_ed_results: list[dict]) -> str:
    lines: list[str] = [
        f"# Op-Ed Debate: {topic}",
        f"*Generated: {timestamp}*",
        "",
        "---",
        "",
        "## Opening Statements",
        "",
    ]
    for item in op_ed_results:
        persona = item["persona"]
        lines.append(f"### {persona['name']} — {persona['tagline']}")
        lines.append(item["text"])
        if item["fact_check_notes"]:
            lines.append("")
            lines.append(f"> ⚠ Fact-check notes: {item['fact_check_notes']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _build_debate_markdown(
    topic: str,
    timestamp: str,
    op_ed_results: list[dict],
    all_rounds: list[dict],
    moderator_summaries: dict[int, str],
) -> str:
    md = _build_opeds_markdown(topic, timestamp, op_ed_results)
    lines: list[str] = [md]

    for rnd in all_rounds:
        round_num = rnd["round"]
        lines.append(f"## Debate — Round {round_num}")
        lines.append("")
        for resp in rnd["responses"]:
            lines.append(f"### {resp['persona_name']}")
            lines.append(resp["text"])
            lines.append("")
            lines.append("---")
            lines.append("")
        if round_num in moderator_summaries:
            lines.append(f"### 🎙 Moderator Summary — Round {round_num}")
            lines.append(moderator_summaries[round_num])
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


@app.command()
def opeds(
    topic: str = typer.Argument(..., help="The topic for op-ed pieces."),
    fact_check: bool = typer.Option(True, "--fact-check/--no-fact-check", help="Run fact-checker on each op-ed."),
    save: bool = typer.Option(False, "--save/--no-save", help="Save output to output/ as a markdown file."),
    persona: str = typer.Option(
        None,
        "--persona",
        help="Generate only one persona's op-ed (use persona ID, e.g. le_tribun).",
    ),
) -> None:
    """Generate opening op-ed pieces on TOPIC from all six French intellectuals."""

    # Header panel
    header = Text(f"Op-Ed Topic: {topic}", style="bold white")
    console.print(Panel(header, style="bold white on dark_blue", padding=(0, 2)))
    console.print()

    # Resolve personas
    if persona:
        if persona not in PERSONAS_BY_ID:
            valid = ", ".join(PERSONAS_BY_ID.keys())
            console.print(
                f"[bold red]Error:[/bold red] Unknown persona ID '{persona}'. "
                f"Valid IDs: {valid}"
            )
            raise typer.Exit(code=1)
        personas_to_run = [PERSONAS_BY_ID[persona]]
    else:
        personas_to_run = ALL_PERSONAS

    op_ed_results = _run_opeds(topic, fact_check, personas_to_run)

    if save and op_ed_results:
        _ensure_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = OUTPUT_DIR / f"{_slug(topic)}_{timestamp}.md"
        md_content = _build_opeds_markdown(topic, timestamp, op_ed_results)
        filename.write_text(md_content, encoding="utf-8")
        console.print(f"\n[bold green]Saved:[/bold green] {filename}")


@app.command()
def debate(
    topic: str = typer.Argument(..., help="The topic for the debate."),
    rounds: int = typer.Option(2, "--rounds", help="Number of debate rounds after opening op-eds."),
    fact_check: bool = typer.Option(True, "--fact-check/--no-fact-check", help="Run fact-checker on opening op-eds."),
    save: bool = typer.Option(False, "--save/--no-save", help="Save full transcript to output/."),
) -> None:
    """Generate op-eds then run multi-round debate with a moderator synthesis."""

    # Header panel
    header = Text(f"Debate Topic: {topic}", style="bold white")
    console.print(Panel(header, style="bold white on dark_blue", padding=(0, 2)))
    console.print()

    # --- Phase 1: Opening op-eds ---
    console.rule("[bold]Opening Statements[/bold]")
    op_ed_results = _run_opeds(topic, fact_check, ALL_PERSONAS)

    # Build the all_op_eds structure needed by the debate engine
    all_op_eds = [
        {"persona_name": item["persona_name"], "text": item["text"]}
        for item in op_ed_results
    ]

    # --- Phase 2: Debate rounds ---
    all_rounds: list[dict] = []
    moderator_summaries: dict[int, str] = {}

    for round_num in range(1, rounds + 1):
        console.print()
        console.rule(f"[bold]Debate — Round {round_num}[/bold]")
        console.print()

        round_responses: list[dict] = []

        for persona in ALL_PERSONAS:
            with console.status(
                f"[bold]{persona['name']}[/bold] is responding (Round {round_num})...",
                spinner="dots",
            ):
                try:
                    response_text = generate_debate_response(
                        persona=persona,
                        topic=topic,
                        round_number=round_num,
                        all_op_eds=all_op_eds,
                        previous_rounds=all_rounds,
                    )
                except Exception as exc:
                    console.print(
                        f"[bold red]Warning:[/bold red] Failed to generate debate response "
                        f"for {persona['name']} in round {round_num}: {exc}"
                    )
                    continue

            _display_debate_response(persona, response_text)
            round_responses.append(
                {"persona_name": persona["name"], "text": response_text}
            )

        # Moderator summary
        if round_responses:
            with console.status(
                "[bold bright_yellow]Modérateur[/bold bright_yellow] is summarising...",
                spinner="dots",
            ):
                try:
                    mod_text = generate_moderator_summary(
                        round_number=round_num,
                        round_responses=round_responses,
                        topic=topic,
                    )
                except Exception as exc:
                    console.print(
                        f"[bold red]Warning:[/bold red] Moderator summary failed for "
                        f"round {round_num}: {exc}"
                    )
                    mod_text = "(Moderator summary unavailable)"

            _display_moderator(mod_text, round_num)
            moderator_summaries[round_num] = mod_text

        all_rounds.append({"round": round_num, "responses": round_responses})

    # --- Phase 3: Save ---
    if save and op_ed_results:
        _ensure_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = OUTPUT_DIR / f"{_slug(topic)}_debate_{timestamp}.md"
        md_content = _build_debate_markdown(
            topic, timestamp, op_ed_results, all_rounds, moderator_summaries
        )
        filename.write_text(md_content, encoding="utf-8")
        console.print(f"\n[bold green]Saved:[/bold green] {filename}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
