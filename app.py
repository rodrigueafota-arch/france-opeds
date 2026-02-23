"""
app.py — Streamlit front-end for the France Op-Ed & Debate Engine.

Replaces the CLI (france_debate.py). Imports from existing backend modules
without modifying them.
"""

from datetime import datetime

import streamlit as st

from debate_engine import generate_debate_response, generate_moderator_summary, generate_op_ed
from fact_checker import fact_check
from personas import ALL_PERSONAS

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Le Débat Français",
    page_icon="🇫🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Serif+4:wght@300;400&display=swap');

h1, h2, h3 { font-family: 'Playfair Display', serif; }
p, div { font-family: 'Source Serif 4', serif; }

.main-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
    border-bottom: 2px solid #C8102E;
    margin-bottom: 2rem;
}

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

.moderator-card {
    background-color: #1a1500;
    border: 1px solid #f0a500;
    padding: 1.5rem;
    margin: 1.5rem 0;
    border-radius: 4px;
    text-align: center;
}

.round-header {
    text-align: center;
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    color: #C8102E;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #333;
}

.section-divider {
    border: none;
    border-top: 1px solid #333;
    margin: 2rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Persona colours
# ---------------------------------------------------------------------------

PERSONA_COLOURS = {
    "le_tribun":       "#C8102E",
    "le_rationaliste": "#00A8CC",
    "le_pragmatique":  "#2ECC71",
    "le_visionnaire":  "#9B59B6",
    "le_patriote":     "#2980B9",
    "l_economiste":    "#F39C12",
}

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "op_eds" not in st.session_state:
    st.session_state.op_eds = []
if "debate_rounds" not in st.session_state:
    st.session_state.debate_rounds = []
if "markdown_transcript" not in st.session_state:
    st.session_state.markdown_transcript = ""
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🇫🇷 Le Débat Français")
    st.divider()

    topic = st.text_input("Topic", placeholder="e.g. La réforme des retraites")
    st.divider()

    mode = st.radio("Mode", ["Op-Eds only", "Op-Eds + Debate"])

    if mode == "Op-Eds + Debate":
        st.divider()
        rounds = st.slider("Debate rounds", min_value=1, max_value=3, value=2)
    else:
        rounds = 2

    st.divider()
    fact_check_enabled = st.checkbox("Fact-check op-eds", value=True)
    st.divider()

    generate_btn = st.sidebar.button("✍ Generate", type="primary", use_container_width=True)

    if st.session_state.markdown_transcript:
        st.divider()
        slug = topic.lower().replace(" ", "_")[:30] if topic else "transcript"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "⬇ Download as Markdown",
            data=st.session_state.markdown_transcript,
            file_name=f"{slug}_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()
    with st.expander("About the personas"):
        for p in ALL_PERSONAS:
            st.markdown(f"**{p['name']}** — *{p['tagline']}*")

# ---------------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------------

st.markdown(
    """
<div class="main-header">
    <h1>🇫🇷 Le Débat Français</h1>
    <p style="color: #888; font-style: italic;">Six voix. Une France.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

if generate_btn:
    if not topic.strip():
        st.sidebar.warning("Please enter a topic.")
    else:
        # Clear previous results
        st.session_state.op_eds = []
        st.session_state.debate_rounds = []
        st.session_state.markdown_transcript = ""
        st.session_state.current_topic = topic

        transcript_lines = [
            f"# Le Débat Français: {topic}",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            "---",
            "",
            "## Opening Statements",
            "",
        ]

        with st.status("Generating op-eds...", expanded=True) as status:
            # --- Op-eds ---
            for persona in ALL_PERSONAS:
                st.write(f"✍ {persona['name']} is writing...")
                try:
                    text = generate_op_ed(persona, topic)
                    fc_notes = ""
                    if fact_check_enabled:
                        fc_result = fact_check(text, persona["name"])
                        text = fc_result["corrected_text"]
                        fc_notes = fc_result["fact_check_notes"]
                    st.session_state.op_eds.append(
                        {"persona": persona, "text": text, "fact_check_notes": fc_notes, "error": None}
                    )
                    transcript_lines += [
                        f"### {persona['name']} — {persona['tagline']}",
                        text,
                    ]
                    if fc_notes:
                        transcript_lines.append(f"> ⚠ Fact-check notes: {fc_notes}")
                    transcript_lines += ["", "---", ""]
                except Exception as exc:
                    st.session_state.op_eds.append(
                        {"persona": persona, "text": "", "fact_check_notes": "", "error": str(exc)}
                    )

            # --- Debate rounds ---
            if mode == "Op-Eds + Debate":
                all_op_eds = [
                    {"persona_name": item["persona"]["name"], "text": item["text"]}
                    for item in st.session_state.op_eds
                    if not item["error"]
                ]
                previous_rounds: list[dict] = []

                for round_num in range(1, rounds + 1):
                    st.write(f"🎙 Debate round {round_num}...")
                    round_responses = []

                    for persona in ALL_PERSONAS:
                        try:
                            response_text = generate_debate_response(
                                persona, topic, round_num, all_op_eds, previous_rounds
                            )
                            round_responses.append(
                                {"persona": persona, "text": response_text, "error": None}
                            )
                        except Exception as exc:
                            round_responses.append(
                                {"persona": persona, "text": "", "error": str(exc)}
                            )

                    valid_responses = [
                        {"persona_name": r["persona"]["name"], "text": r["text"]}
                        for r in round_responses
                        if not r["error"]
                    ]
                    try:
                        moderator_text = generate_moderator_summary(
                            round_num, valid_responses, topic
                        )
                    except Exception as exc:
                        moderator_text = f"Moderator summary failed: {exc}"

                    st.session_state.debate_rounds.append(
                        {"round": round_num, "responses": round_responses, "moderator": moderator_text}
                    )
                    previous_rounds.append({"round": round_num, "responses": valid_responses})

                    transcript_lines += [f"## Debate — Round {round_num}", ""]
                    for r in round_responses:
                        body = r["text"] if not r["error"] else f"*Error: {r['error']}*"
                        transcript_lines += [f"### {r['persona']['name']}", body, "", "---", ""]
                    transcript_lines += ["### 🎙 Modérateur", moderator_text, "", "---", ""]

            st.session_state.markdown_transcript = "\n".join(transcript_lines)
            status.update(label="Done ✓", state="complete")

        st.rerun()

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

if st.session_state.op_eds:
    # Op-eds: 2-column grid
    cols = st.columns(2)
    for i, item in enumerate(st.session_state.op_eds):
        persona = item["persona"]
        color = PERSONA_COLOURS.get(persona["id"], "#888888")
        with cols[i % 2]:
            if item["error"]:
                st.markdown(
                    f"""
<div class="persona-card" style="--card-color:{color}; border-left-color:{color};">
    <div class="persona-name">{persona['name']}</div>
    <div class="persona-tagline">{persona['tagline']}</div>
    <div style="color:#C8102E;">⚠ Generation failed: {item['error']}</div>
</div>""",
                    unsafe_allow_html=True,
                )
            else:
                fc_html = ""
                if item["fact_check_notes"]:
                    fc_html = (
                        f'<div class="fact-check-note">⚠ Fact-check notes:<br>'
                        f'{item["fact_check_notes"]}</div>'
                    )
                body_html = item["text"].replace("\n", "<br>")
                st.markdown(
                    f"""
<div class="persona-card" style="--card-color:{color}; border-left-color:{color};">
    <div class="persona-name">{persona['name']}</div>
    <div class="persona-tagline">{persona['tagline']}</div>
    <div class="op-ed-text">{body_html}</div>
    {fc_html}
</div>""",
                    unsafe_allow_html=True,
                )

    # Debate rounds: full-width
    for rnd in st.session_state.debate_rounds:
        st.markdown(
            f'<div class="round-header">⚔ Debate — Round {rnd["round"]}</div>',
            unsafe_allow_html=True,
        )
        for r in rnd["responses"]:
            persona = r["persona"]
            color = PERSONA_COLOURS.get(persona["id"], "#888888")
            if r["error"]:
                st.markdown(
                    f"""
<div class="persona-card" style="--card-color:{color}; border-left-color:{color};">
    <div class="persona-name">{persona['name']}</div>
    <div class="persona-tagline">{persona['tagline']}</div>
    <div style="color:#C8102E;">⚠ Generation failed: {r['error']}</div>
</div>""",
                    unsafe_allow_html=True,
                )
            else:
                body_html = r["text"].replace("\n", "<br>")
                st.markdown(
                    f"""
<div class="persona-card" style="--card-color:{color}; border-left-color:{color};">
    <div class="persona-name">{persona['name']}</div>
    <div class="persona-tagline">{persona['tagline']}</div>
    <div class="op-ed-text">{body_html}</div>
</div>""",
                    unsafe_allow_html=True,
                )

        moderator_html = rnd["moderator"].replace("\n", "<br>")
        st.markdown(
            f"""
<div class="moderator-card">
    <div style="font-style:italic; color:#f0a500; margin-bottom:0.5rem;">🎙 Modérateur</div>
    <div>{moderator_html}</div>
</div>""",
            unsafe_allow_html=True,
        )

else:
    # Empty state
    st.markdown(
        """
<div style="text-align:center; padding:3rem 0; color:#666;">
    <p style="font-size:1.1rem;">Six French intellectual voices debate the issues that define France.</p>
    <p>Enter a topic in the sidebar and press Generate.</p>
</div>""",
        unsafe_allow_html=True,
    )
    # Persona preview grid
    grid_cols = st.columns(3)
    for i, persona in enumerate(ALL_PERSONAS):
        color = PERSONA_COLOURS.get(persona["id"], "#888888")
        with grid_cols[i % 3]:
            st.markdown(
                f"""
<div class="persona-card" style="--card-color:{color}; border-left-color:{color}; opacity:0.65;">
    <div class="persona-name">{persona['name']}</div>
    <div class="persona-tagline">{persona['tagline']}</div>
</div>""",
                unsafe_allow_html=True,
            )
