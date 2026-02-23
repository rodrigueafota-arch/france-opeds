"""
debate_engine.py — Orchestrates op-ed generation and multi-round debates.

Uses the Claude Code CLI (`claude -p`) instead of the Anthropic SDK,
so no API key is required — only a Claude Code subscription.
"""

import subprocess

from personas import ALL_PERSONAS, PERSONAS_BY_ID, MODERATOR_SYSTEM_PROMPT  # noqa: F401

_DEBATE_SUFFIX = (
    "\n\nYou are now in a live debate. You have read the other contributors' pieces and responses. "
    "Write a response of 100-120 words. Address at least one other contributor by name. "
    "Be direct. You may agree partially, disagree sharply, or reframe the debate entirely. "
    "Stay in character."
)


def _call_claude(system_prompt: str, user_message: str) -> str:
    """Call Claude via the Claude Code CLI using the current subscription."""
    combined_prompt = f"{system_prompt}\n\n{user_message}"
    result = subprocess.run(
        ["claude", "-p", combined_prompt],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    return result.stdout.strip()


def generate_op_ed(persona: dict, topic: str) -> str:
    """
    Generate an opening op-ed for a persona on a given topic.

    Parameters
    ----------
    persona: A persona dict from personas.py (must have "system_prompt").
    topic:   The debate topic string.

    Returns
    -------
    The raw text of the generated op-ed.
    """
    return _call_claude(
        persona["system_prompt"],
        f"Write your op-ed on the following topic: {topic}",
    )


def generate_debate_response(
    persona: dict,
    topic: str,
    round_number: int,
    all_op_eds: list[dict],
    previous_rounds: list[dict],
) -> str:
    """
    Generate a persona's response for a single debate round.

    Parameters
    ----------
    persona:         Persona dict.
    topic:           Debate topic string.
    round_number:    Current round number (1-based).
    all_op_eds:      List of dicts: [{"persona_name": str, "text": str}, ...]
    previous_rounds: List of dicts: [{"round": int, "responses": [{"persona_name": str, "text": str}]}, ...]

    Returns
    -------
    The raw text of the debate response.
    """
    # Build context block
    context_lines: list[str] = ["=== Opening Statements ==="]
    for item in all_op_eds:
        context_lines.append(f"\n--- {item['persona_name']} ---\n{item['text']}")

    for rnd in previous_rounds:
        context_lines.append(f"\n=== Debate Round {rnd['round']} ===")
        for resp in rnd["responses"]:
            context_lines.append(f"\n--- {resp['persona_name']} ---\n{resp['text']}")

    context_block = "\n".join(context_lines)
    user_message = (
        f"{context_block}\n\nRound {round_number}: Respond to the debate on: {topic}"
    )

    system_prompt = persona["system_prompt"] + _DEBATE_SUFFIX

    return _call_claude(system_prompt, user_message)


def generate_moderator_summary(
    round_number: int, round_responses: list[dict], topic: str
) -> str:
    """
    Generate the moderator's synthesis after a debate round.

    Parameters
    ----------
    round_number:    The round that just concluded.
    round_responses: List of dicts: [{"persona_name": str, "text": str}, ...]
    topic:           The debate topic.

    Returns
    -------
    The moderator's synthesis text.
    """
    response_block_lines: list[str] = []
    for resp in round_responses:
        response_block_lines.append(f"--- {resp['persona_name']} ---\n{resp['text']}")
    response_block = "\n\n".join(response_block_lines)

    user_message = (
        f"The following are the Round {round_number} responses in the debate on: {topic}\n\n"
        f"{response_block}\n\n"
        "Please provide your moderator synthesis."
    )

    return _call_claude(MODERATOR_SYSTEM_PROMPT, user_message)
