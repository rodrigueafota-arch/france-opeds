"""
fact_checker.py — Fact-checking logic using the Anthropic Python SDK.
"""

import anthropic

from personas import FACT_CHECKER_SYSTEM_PROMPT

_client = anthropic.Anthropic()


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

    try:
        message = _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=FACT_CHECKER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        full_response = message.content[0].text.strip()
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
