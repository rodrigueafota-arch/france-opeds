# France Op-Ed & Debate Engine — Streamlit Front-End Brief

## Context

The backend is already built. It consists of:
- `personas.py` — 6 persona definitions + fact-checker and moderator prompts
- `debate_engine.py` — functions: `generate_op_ed`, `generate_debate_response`, `generate_moderator_summary`
- `fact_checker.py` — function: `fact_check`

Do not modify any of these files. Import from them directly.

The goal is to build a Streamlit web app that replaces the CLI, deployable to Streamlit Community Cloud.

---

## New Files to Create

```
france-opeds/
├── app.py                        # Streamlit app — the only new main file
├── .streamlit/
│   └── config.toml               # Streamlit theme configuration
├── requirements.txt              # UPDATE to add streamlit
└── README.md                     # UPDATE with Streamlit deployment instructions
```

Do not create any other new files.

---

## Dependencies

Add `streamlit>=1.35.0` to `requirements.txt`. The full file should be:

```
anthropic>=0.25.0
python-dotenv>=1.0.0
streamlit>=1.35.0
```

Remove `rich` and `typer` — they are CLI-only and not needed in the Streamlit app.

---

## Streamlit Theme

Create `.streamlit/config.toml` with the following theme — dark, editorial, serious:

```toml
[theme]
primaryColor = "#C8102E"
backgroundColor = "#0F0F0F"
secondaryBackgroundColor = "#1A1A1A"
textColor = "#F0F0F0"
font = "serif"
```

---

## App Structure (`app.py`)

### Imports and setup

```python
import streamlit as st
from debate_engine import generate_op_ed, generate_debate_response, generate_moderator_summary
from fact_checker import fact_check
from personas import ALL_PERSONAS, PERSONAS_BY_ID
import os
from dotenv import load_dotenv
from datetime import datetime
```

Load `.env` at the top. Check that `ANTHROPIC_API_KEY` is set; if not, call `st.error()` and `st.stop()`.

### Page config

```python
st.set_page_config(
    page_title="Le Débat Français",
    page_icon="🇫🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

---

## Custom CSS

Inject the following CSS via `st.markdown(..., unsafe_allow_html=True)` immediately after page config. This is critical for the visual quality:

```css
<style>
/* Typography */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Serif+4:wght@300;400&display=swap');

h1, h2, h3 { font-family: 'Playfair Display', serif; }
p, div { font-family: 'Source Serif 4', serif; }

/* Main header */
.main-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
    border-bottom: 2px solid #C8102E;
    margin-bottom: 2rem;
}

/* Persona card */
.persona-card {
    background-color: #1A1A1A;
    border-left: 4px solid var(--card-color);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-radius: 0 4px 4px 0;
}

.persona-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.persona-tagline {
    font-style: italic;
    color: #888;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.op-ed-text {
    line-height: 1.8;
    font-size: 1rem;
}

.fact-check-note {
    background-color: #2a1f00;
    border-left: 3px solid #f0a500;
    padding: 0.75rem 1rem;
    margin-top: 1rem;
    font-size: 0.85rem;
    color: #f0a500;
    font-family: monospace;
}

/* Moderator */
.moderator-card {
    background-color: #1a1500;
    border: 1px solid #f0a500;
    padding: 1.5rem;
    margin: 1.5rem 0;
    border-radius: 4px;
    text-align: center;
}

/* Round header */
.round-header {
    text-align: center;
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    color: #C8102E;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #333;
}

/* Divider */
.section-divider {
    border: none;
    border-top: 1px solid #333;
    margin: 2rem 0;
}
</style>
```

---

## Sidebar

The sidebar contains all controls:

```
🇫🇷  Le Débat Français
────────────────────────
Topic input (text_input)
────────────────────────
Mode
  ○ Op-Eds only
  ○ Op-Eds + Debate
────────────────────────
[if debate mode]
Debate rounds (slider 1–3, default 2)
────────────────────────
Options
  ☑ Fact-check op-eds
────────────────────────
[Generate button]
────────────────────────
[if results exist]
[Download as Markdown button]
────────────────────────
About (expander)
  Brief description of each persona (name + one-line bio)
```

Use `st.sidebar` for all of the above. The Generate button should be `st.sidebar.button("✍ Generate", type="primary", use_container_width=True)`.

The Download button uses `st.sidebar.download_button` with the markdown transcript as the file content. Only show it after a successful generation.

---

## Persona Colours

Define this dict in `app.py` and use it to set `--card-color` inline style on each persona card:

```python
PERSONA_COLOURS = {
    "le_tribun":      "#C8102E",
    "le_rationaliste": "#00A8CC",
    "le_pragmatique": "#2ECC71",
    "le_visionnaire": "#9B59B6",
    "le_patriote":    "#2980B9",
    "l_economiste":   "#F39C12",
}
```

---

## Main Content Area

### Header

```
🇫🇷  Le Débat Français

[ tagline in italic grey: "Six voix. Une France." ]
```

### Empty state (before generation)

When no results exist yet, show a centred placeholder:

```
Six French intellectual voices debate the issues that define France.

Enter a topic in the sidebar and press Generate.

[ subtle grid showing the 6 persona names and archetypes as cards ]
```

### Results layout

Use `st.columns(2)` to show op-eds in a 2-column grid (3 rows × 2 columns). Assign personas to columns alternating left-right in the order they appear in `ALL_PERSONAS`.

Each op-ed renders as a styled HTML block using `st.markdown(..., unsafe_allow_html=True)` with the `.persona-card` CSS class and the persona's border colour set as an inline CSS variable.

Below each op-ed, if fact-check notes are non-empty, render the `.fact-check-note` div.

For debate rounds, switch to a single full-width column layout. Each response gets its own persona card. After all 6 responses in a round, render the moderator card full-width.

---

## State Management

Use `st.session_state` to store results so the page does not re-run API calls on widget interaction:

```python
if "op_eds" not in st.session_state:
    st.session_state.op_eds = []

if "debate_rounds" not in st.session_state:
    st.session_state.debate_rounds = []

if "markdown_transcript" not in st.session_state:
    st.session_state.markdown_transcript = ""

if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
```

Clear all state when the user changes the topic or presses Generate again.

---

## Generation Flow

When the Generate button is pressed:

1. Validate that the topic field is not empty; if empty, `st.sidebar.warning("Please enter a topic.")`
2. Clear session state
3. Show a full-width `st.status("Generating op-eds...")` context manager
4. Inside the status block, loop through `ALL_PERSONAS`:
   - `st.write(f"✍ {persona['real_name']} is writing...")` 
   - Call `generate_op_ed(persona, topic)`
   - If fact-check enabled, call `fact_check(result, persona['name'])`
   - Append to `st.session_state.op_eds`
5. If debate mode:
   - For each round:
     - Update status: `st.write(f"🎙 Debate round {n}...")`
     - Loop through personas, call `generate_debate_response`
     - Call `generate_moderator_summary`
     - Append to `st.session_state.debate_rounds`
6. Build `st.session_state.markdown_transcript` (same format as CLI save output)
7. Status block closes with `st.status("Done ✓", state="complete")`
8. `st.rerun()` to re-render with results

---

## Markdown Transcript Format

Build the transcript string during generation and store in session state. Use this format:

```markdown
# Le Débat Français: {topic}
*Generated: {timestamp}*

---

## Opening Statements

### {Persona Name} — {tagline}
{op-ed text}

> ⚠ Fact-check notes: {notes}

---

## Debate — Round {n}

### {Persona Name}
{response}

---

### 🎙 Modérateur
{moderator summary}

---
```

---

## Error Handling

- Wrap every `generate_*` and `fact_check` call in try/except
- On failure, store an error string in the result dict and render it as a red warning card instead of the op-ed
- Never let a single persona failure crash the whole generation run
- If `ANTHROPIC_API_KEY` is not set, show `st.error` and `st.stop()` before rendering anything

---

## Deployment Instructions (add to README.md)

Add a new section to `README.md`:

```markdown
## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (public or private)
2. Go to share.streamlit.io and sign in with GitHub
3. Click "New app" → select your repo → set Main file path to `app.py`
4. Under "Advanced settings" → "Secrets", add:
   ANTHROPIC_API_KEY = "your_key_here"
5. Click Deploy. The app will be live at a public URL within 2 minutes.

Note: do NOT commit your .env file to GitHub. The API key is set via Streamlit secrets only.
```

Also add to `.gitignore` (create if missing):
```
.env
__pycache__/
*.pyc
output/
```

---

## Acceptance Criteria

- [ ] `streamlit run app.py` launches without errors locally
- [ ] Entering a topic and pressing Generate produces 6 styled op-eds in a 2-column layout
- [ ] Fact-check notes appear below any op-ed that has them
- [ ] Debate mode produces responses and moderator summaries per round
- [ ] Download button produces a valid `.md` file
- [ ] The app does not crash if one API call fails — it shows an error card for that persona only
- [ ] Deployed to Streamlit Community Cloud and accessible via public URL
- [ ] API key is set via Streamlit secrets, not committed to the repo
