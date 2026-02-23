# France Op-Ed & Debate Engine — Build Brief for Claude Code

## Project Overview

Build a Python CLI application that simulates six French intellectual contributors writing op-ed pieces and debating each other on topics related to France: its society, economy, history, politics, and culture. The app uses the Anthropic Python SDK to generate content via the Claude API.

The `personas.py` file is already written and provided separately. Do not rewrite it. Import from it directly.

---

## Repository Structure

Create the following file and folder structure exactly:

```
france-opeds/
├── personas.py              # PROVIDED — do not modify
├── france_debate.py         # Main CLI entry point
├── debate_engine.py         # Orchestrates op-ed generation and multi-round debates
├── fact_checker.py          # Fact-checking logic using a second API call
├── output/                  # Directory for saved markdown outputs (create if missing)
├── requirements.txt         # Python dependencies
├── .env.example             # Example env file (never write a real .env)
└── README.md                # Usage instructions
```

---

## Dependencies

Use the following. Write them into `requirements.txt`:

```
anthropic>=0.25.0
python-dotenv>=1.0.0
rich>=13.0.0
typer>=0.12.0
```

- `anthropic` — Anthropic Python SDK for all API calls
- `python-dotenv` — load `ANTHROPIC_API_KEY` from a `.env` file
- `rich` — formatted terminal output (panels, colours, spinners)
- `typer` — CLI argument and option handling

---

## Environment

Load `ANTHROPIC_API_KEY` from a `.env` file using `python-dotenv`. Never hardcode the key. Write an `.env.example` with:

```
ANTHROPIC_API_KEY=your_key_here
```

---

## Models

- **Op-ed generation and debate**: `claude-sonnet-4-5` (balance of quality and cost)
- **Fact-checking**: `claude-haiku-4-5-20251001` (fast and cheap for the review pass)

Both model strings must be defined as constants at the top of `debate_engine.py` and `fact_checker.py` respectively, so they are easy to change.

---

## Module Specifications

### `fact_checker.py`

- Import `FACT_CHECKER_SYSTEM_PROMPT` from `personas.py`
- Expose a single public function:

```python
def fact_check(op_ed_text: str, persona_name: str) -> dict:
    ...
```

- It must make one API call using `claude-haiku-4-5-20251001`
- The user message should be: `f"Please fact-check the following op-ed by {persona_name}:\n\n{op_ed_text}"`
- Return a dict with two keys:
  - `"corrected_text"` — the revised op-ed (or original if nothing changed)
  - `"fact_check_notes"` — the notes section from the model's response (empty string if none)
- Parse the model response by splitting on `"Fact-check notes"` if present; otherwise treat the full response as `corrected_text` with empty notes
- Handle API errors gracefully: on failure, return the original text with a note saying fact-checking failed

---

### `debate_engine.py`

Import from `personas.py`:
- `ALL_PERSONAS`
- `PERSONAS_BY_ID`
- `MODERATOR_SYSTEM_PROMPT`

#### Function: `generate_op_ed`

```python
def generate_op_ed(persona: dict, topic: str) -> str:
    ...
```

- Makes one API call using `claude-sonnet-4-5`
- System prompt: `persona["system_prompt"]`
- User message: `f"Write your op-ed on the following topic: {topic}`
- `max_tokens`: 600
- Returns the raw text response

#### Function: `generate_debate_response`

```python
def generate_debate_response(persona: dict, topic: str, round_number: int, all_op_eds: list[dict], previous_rounds: list[dict]) -> str:
    ...
```

- `all_op_eds` is a list of dicts: `[{"persona_name": str, "text": str}, ...]`
- `previous_rounds` is a list of dicts: `[{"round": int, "responses": [{"persona_name": str, "text": str}]}, ...]`
- Builds a context block from all op-eds and previous round responses
- System prompt: `persona["system_prompt"]` plus the following appended paragraph:

```
You are now in a live debate. You have read the other contributors' pieces and responses. 
Write a response of 100-120 words. Address at least one other contributor by name. 
Be direct. You may agree partially, disagree sharply, or reframe the debate entirely. 
Stay in character.
```

- User message: the full context block followed by `f"Round {round_number}: Respond to the debate on: {topic}"`
- `max_tokens`: 300
- Returns the raw text response

#### Function: `generate_moderator_summary`

```python
def generate_moderator_summary(round_number: int, round_responses: list[dict], topic: str) -> str:
    ...
```

- Uses `MODERATOR_SYSTEM_PROMPT` as the system prompt
- User message: the round's responses formatted as a block, asking for a synthesis
- Model: `claude-sonnet-4-5`
- `max_tokens`: 200
- Returns the moderator's synthesis text

---

### `france_debate.py`

This is the CLI entry point built with `typer`. It must support two commands:

#### Command 1: `opeds`

```
python france_debate.py opeds "La réforme des retraites"
```

**Options:**
- `--fact-check / --no-fact-check` — default `True`; run the fact-checker on each op-ed
- `--save / --no-save` — default `False`; save output to `output/` as a markdown file
- `--persona` — optional; one of the persona IDs (e.g. `le_tribun`); if provided, generate only that persona's op-ed

**Behaviour:**
1. Print a header panel with the topic
2. For each of the 6 personas (or just the selected one):
   a. Show a `rich` spinner: `"Gilles de Mareschal is writing..."`
   b. Call `generate_op_ed`
   c. If `--fact-check`, call `fact_check`; if notes are non-empty, append a collapsible note below the op-ed: `"⚠ Fact-check notes: {notes}"`
   d. Display the op-ed in a `rich` Panel with the persona name and tagline as the title
3. If `--save`, write all op-eds (and fact-check notes) to `output/{slug_topic}_{timestamp}.md`

#### Command 2: `debate`

```
python france_debate.py debate "La réforme des retraites"
```

**Options:**
- `--rounds` — integer, default `2`; number of debate rounds after the opening op-eds
- `--fact-check / --no-fact-check` — default `True`
- `--save / --no-save` — default `False`

**Behaviour:**
1. Run the `opeds` flow first (with fact-checking if enabled) to generate opening statements
2. For each round from 1 to `--rounds`:
   a. Print a round header
   b. For each persona, show a spinner and call `generate_debate_response` passing all opening op-eds and all previous round responses
   c. Display each response in a styled panel
   d. After all 6 have responded, call `generate_moderator_summary` and display it in a distinct moderator panel (different colour — use `yellow`)
3. If `--save`, write the full transcript (op-eds + all rounds + moderator summaries) to `output/{slug_topic}_debate_{timestamp}.md`

---

## Output / Saved Markdown Format

When saving, use this structure:

```markdown
# Op-Ed Debate: {topic}
*Generated: {timestamp}*

---

## Opening Statements

### {Persona Name} — {tagline}
{op-ed text}

> ⚠ Fact-check notes: {notes}   ← only if non-empty

---

## Debate — Round {n}

### {Persona Name}
{response text}

---

### 🎙 Moderator Summary — Round {n}
{moderator text}

---
```

---

## Rich Terminal Styling

Use `rich` for all output. Apply consistent styling:

| Element | Style |
|---|---|
| Topic header | Bold white on dark blue panel |
| Le Tribun | Panel border: `red` |
| Le Rationaliste | Panel border: `cyan` |
| Le Pragmatique | Panel border: `green` |
| Le Visionnaire | Panel border: `magenta` |
| Le Patriote | Panel border: `blue` |
| L'Économiste | Panel border: `yellow` |
| Moderator | Panel border: `bright_yellow`, title: `🎙 Modérateur` |
| Fact-check warning | `rich` `Text` in `orange1` below the panel |
| Spinners | `rich` `Progress` or `Status` with persona-specific messages |

Define a `PERSONA_COLOURS` dict in `france_debate.py` keyed by persona ID.

---

## Error Handling

- If `ANTHROPIC_API_KEY` is missing, print a clear error and exit with code 1
- If any single API call fails, print a warning in red and continue with the remaining personas rather than crashing the whole run
- If the `output/` directory does not exist, create it automatically
- Wrap all API calls in try/except blocks

---

## README.md

Write a clear `README.md` covering:
1. What the project does (2–3 sentences)
2. Installation (`pip install -r requirements.txt`)
3. Setup (copy `.env.example` to `.env`, add API key)
4. Usage examples for both `opeds` and `debate` commands, including all flags
5. A one-line description of each persona
6. A note that `personas.py` can be edited to tune voices and add new contributors

---

## Important Constraints

- Do not use `asyncio` or async API calls; keep everything synchronous for simplicity
- Do not use `langchain`, `llama-index`, or any orchestration framework; call the Anthropic SDK directly
- Do not use `localStorage`, databases, or any persistent state beyond the saved markdown files
- The app must run fully from the terminal with no web server
- All generated text must be treated as potentially containing factual errors until the fact-checker has run
- Never print the raw API response object; always extract `.content[0].text`

---

## Acceptance Criteria

The build is complete when:

- [ ] `python france_debate.py opeds "L'immigration en France"` runs end-to-end and prints 6 styled op-eds
- [ ] `python france_debate.py debate "La réforme des retraites" --rounds 2` runs and prints op-eds, 2 debate rounds, and 2 moderator summaries
- [ ] `--save` produces a valid, readable markdown file in `output/`
- [ ] `--persona le_tribun` generates only Le Tribun's op-ed
- [ ] `--no-fact-check` skips the fact-checking pass without errors
- [ ] A missing `.env` file produces a clean error message, not a Python traceback
- [ ] All 6 personas use their correct `system_prompt` from `personas.py` without modification
