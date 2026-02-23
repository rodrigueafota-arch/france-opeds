"""
fact_checker.py — Fact-checking logic using the Anthropic Python SDK.
"""

from debate_engine import call_claude
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
    try:
        response = call_claude(
            system_prompt=FACT_CHECKER_SYSTEM_PROMPT,
            user_message=f"Please fact-check the following op-ed by {persona_name}:\n\n{op_ed_text}",
        )
        if "Fact-check notes" in response:
            parts = response.split("Fact-check notes", 1)
            return {
                "corrected_text": parts[0].strip(),
                "fact_check_notes": parts[1].strip(),
            }
        return {"corrected_text": response, "fact_check_notes": ""}
    except Exception as exc:
        return {"corrected_text": op_ed_text, "fact_check_notes": f"Fact-checking failed: {exc}"}
