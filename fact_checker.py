"""
fact_checker.py — Fact-checking logic using the Claude Code CLI.

Uses `claude -p` (Claude Code subscription) instead of the Anthropic SDK,
so no API key is required.
"""

import subprocess

from personas import FACT_CHECKER_SYSTEM_PROMPT


def fact_check(op_ed_text: str, persona_name: str) -> dict:
    """
    Fact-check an op-ed piece.

    Parameters
    ----------
    op_ed_text:   The full text of the op-ed to review.
    persona_name: The display name of the persona who wrote the op-ed.

    Returns
    -------
    A dict with two keys:
      "corrected_text"   — revised op-ed, or original if nothing changed
      "fact_check_notes" — bulleted notes from the model (empty string if none)
    """
    user_message = (
        f"Please fact-check the following op-ed by {persona_name}:\n\n{op_ed_text}"
    )
    combined_prompt = f"{FACT_CHECKER_SYSTEM_PROMPT}\n\n{user_message}"

    try:
        result = subprocess.run(
            ["claude", "-p", combined_prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        full_response = result.stdout.strip()
    except Exception as exc:
        return {
            "corrected_text": op_ed_text,
            "fact_check_notes": f"Fact-checking failed: {exc}",
        }

    # Split on "Fact-check notes" heading if present
    if "Fact-check notes" in full_response:
        parts = full_response.split("Fact-check notes", maxsplit=1)
        corrected_text = parts[0].strip()
        fact_check_notes = parts[1].strip().lstrip(":").strip()
    else:
        corrected_text = full_response.strip()
        fact_check_notes = ""

    return {
        "corrected_text": corrected_text,
        "fact_check_notes": fact_check_notes,
    }
