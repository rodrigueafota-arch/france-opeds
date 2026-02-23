# France Op-Ed & Debate Engine

A Python CLI application that simulates six French intellectual contributors writing op-ed pieces and debating each other on topics related to France — its society, economy, history, politics, and culture. All content is generated via the Anthropic Claude API. Each persona has a distinct voice, ideological position, and rhetorical style, producing genuinely varied takes on any given topic.

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Setup

1. Copy the example env file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and replace `your_key_here` with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

---

## Usage

### Generate op-eds

```bash
# All six personas write on a topic
python france_debate.py opeds "La réforme des retraites"

# Skip fact-checking (faster, no second API pass)
python france_debate.py opeds "La réforme des retraites" --no-fact-check

# Only one persona writes
python france_debate.py opeds "L'immigration en France" --persona le_tribun

# Save output to a markdown file in output/
python france_debate.py opeds "La crise du logement" --save
```

### Run a full debate

```bash
# Two debate rounds (default)
python france_debate.py debate "La réforme des retraites"

# Custom number of rounds
python france_debate.py debate "L'intelligence artificielle" --rounds 3

# Skip fact-checking on opening op-eds
python france_debate.py debate "La laïcité" --no-fact-check

# Save full transcript to output/
python france_debate.py debate "La réforme des retraites" --rounds 2 --save
```

### All flags at a glance

| Flag | Command | Default | Description |
|---|---|---|---|
| `--fact-check / --no-fact-check` | `opeds`, `debate` | `--fact-check` | Run fact-checker on each op-ed |
| `--save / --no-save` | `opeds`, `debate` | `--no-save` | Save output to `output/` as markdown |
| `--persona <id>` | `opeds` | all personas | Generate only one persona's op-ed |
| `--rounds <n>` | `debate` | `2` | Number of debate rounds |

---

## The Six Personas

| Persona ID | Name | Voice |
|---|---|---|
| `le_tribun` | Gilles de Mareschal | Left-wing populist; passionate, rhetorical, speaks for *le peuple* |
| `le_rationaliste` | Dr. Sophie Archambault | Political scientist; evidence-driven, empirical, anti-rhetoric |
| `le_pragmatique` | Marc Fontaine | Centrist former minister; solution-focused, managerial, EU-friendly |
| `le_visionnaire` | Yasmine Belkacemi | Franco-Algerian essayist; postcolonial, intersectional, lyrical |
| `le_patriote` | Colonel (ret.) Henri Brossard | Gaullist-nationalist; sovereigntist, measured, pro-French identity |
| `l_economiste` | Prof. Édouard Vasseur | HEC economist; classical liberal, pro-market, fiscally hawkish |

---

## Customisation

`personas.py` can be edited to:
- Tune any persona's voice, ideology, or rhetorical style by modifying their `system_prompt`.
- Add new contributor personas by appending a new dict to `ALL_PERSONAS`.
- Adjust the moderator's synthesis style via `MODERATOR_SYSTEM_PROMPT`.
- Adjust the fact-checker's behaviour via `FACT_CHECKER_SYSTEM_PROMPT`.

No other files need to change when personas are added or modified.

---

## Output

Saved files are written to the `output/` directory (created automatically if missing) as markdown files named `{topic_slug}_{timestamp}.md` (op-eds) or `{topic_slug}_debate_{timestamp}.md` (full debate transcript).

---

## Streamlit Web App

Run locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (public or private)
2. Go to share.streamlit.io and sign in with GitHub
3. Click "New app" → select your repo → set Main file path to `app.py`
4. Under "Advanced settings" → "Secrets", add:
   ```
   ANTHROPIC_API_KEY = "your_key_here"
   ```
5. Click Deploy. The app will be live at a public URL within 2 minutes.

Note: do NOT commit your .env file to GitHub. The API key is set via Streamlit secrets only.
