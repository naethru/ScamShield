import json

import streamlit as st
import streamlit.components.v1 as components

from rules import analyze_message, get_chatbot_response


st.set_page_config(
    page_title="ScamShield",
    page_icon="scamshield_icon.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

defaults = {
    "font_size": 22,
    "speech_speed": 0.9,
    "scanned_text": "",
    "current_flags": [],
    "scam_score": None,
    "model_available": False,
    "analysis_verdict": "",
    "has_analyzed": False,
    "chat_history": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


logo_col, title_col = st.columns([1, 5], vertical_alignment="center")

with logo_col:
    st.image("scamshield_icon.png", width=82)

with title_col:
    st.title("ScamShield")
    st.markdown("A calm, clear way to review a message before you respond.")

st.markdown("### Follow these three steps")
st.markdown(
    "1. Paste or type the message.\n"
    "2. Select Scan message.\n"
    "3. Review the estimate and warning signs before you respond."
)
st.caption(
    "Remove personal details before pasting. Never include passwords, "
    "sign-in codes, or account numbers."
)


text_size_col, speech_speed_col = st.columns(2, gap="large")

with text_size_col:
    with st.container(key="text_size_panel"):
        st.markdown("### Make text easier to read")
        size_display = st.empty()
        smaller_col, larger_col = st.columns(2, gap="small")

        with smaller_col:
            if st.button(
                "Make text smaller",
                key="smaller_text",
                disabled=st.session_state.font_size <= 18,
            ):
                st.session_state.font_size = max(18, st.session_state.font_size - 2)

        with larger_col:
            if st.button(
                "Make text larger",
                key="larger_text",
                disabled=st.session_state.font_size >= 34,
            ):
                st.session_state.font_size = min(34, st.session_state.font_size + 2)

        size_display.markdown(
            f"Current text size: **{st.session_state.font_size} px**"
        )
        st.caption("Each press changes the text size a little.")

with speech_speed_col:
    with st.container(key="speech_speed_panel"):
        st.markdown("### Choose a reading speed")
        pace_display = st.empty()
        slower_col, faster_col = st.columns(2, gap="small")

        with slower_col:
            if st.button(
                "Slow down reading",
                key="slower_reading",
                disabled=st.session_state.speech_speed <= 0.5,
            ):
                st.session_state.speech_speed = round(
                    max(0.5, st.session_state.speech_speed - 0.1), 1
                )

        with faster_col:
            if st.button(
                "Speed up reading",
                key="faster_reading",
                disabled=st.session_state.speech_speed >= 1.5,
            ):
                st.session_state.speech_speed = round(
                    min(1.5, st.session_state.speech_speed + 0.1), 1
                )

        speed_label = (
            "Slow" if st.session_state.speech_speed < 0.8
            else "Steady" if st.session_state.speech_speed <= 1.1
            else "Fast"
        )
        pace_display.markdown(f"Current pace: **{speed_label}**")
        st.caption("Adjust this before selecting the read-aloud button.")

st.html(
    f"""
    <style>
    :root {{
        color-scheme: light;
        --sapphire: #1A365D;
        --sapphire-dark: #142B4C;
        --workspace: #F7FAFC;
        --paper: #FFFFFF;
        --ink: #102A43;
        --muted: #334E68;
        --amber: #D69E2E;
        --amber-wash: #FFF4D6;
        --line: #9FB3C8;
    }}

    html, body, .stApp, [data-testid="stAppViewContainer"] {{
        background: var(--sapphire) !important;
        color: var(--ink) !important;
        font-family: Arial, sans-serif !important;
    }}

    [data-testid="stHeader"] {{
        background: var(--sapphire) !important;
    }}

    [data-testid="stMainBlockContainer"] {{
        max-width: 1040px;
        margin: 1.5rem auto 2.5rem;
        padding: 2.5rem !important;
        background: var(--workspace) !important;
        border: 1px solid #D5E0EA;
        border-radius: 24px;
        box-shadow: 0 16px 42px rgba(7, 22, 41, 0.24);
    }}

    .stApp p,
    .stApp label,
    .stApp li,
    .stApp [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"] {{
        color: var(--ink) !important;
        font-size: {st.session_state.font_size}px !important;
        line-height: 1.6 !important;
    }}

    h1, h2, h3, h4 {{
        color: var(--sapphire) !important;
        font-weight: 750 !important;
        letter-spacing: -0.02em;
    }}

    h1 {{ font-size: {min(52, int(st.session_state.font_size * 1.9))}px !important; }}
    h2 {{ font-size: {min(38, int(st.session_state.font_size * 1.4))}px !important; }}
    h3 {{ font-size: {min(32, int(st.session_state.font_size * 1.15))}px !important; }}

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {{
        color: var(--muted) !important;
        font-size: {max(16, int(st.session_state.font_size * 0.8))}px !important;
        line-height: 1.55 !important;
    }}

    [data-testid="stTextArea"] textarea {{
        background: var(--paper) !important;
        color: var(--ink) !important;
        border: 2px solid var(--sapphire) !important;
        border-radius: 14px !important;
        font-size: {st.session_state.font_size}px !important;
        line-height: 1.6 !important;
        padding: 16px !important;
    }}

    [data-testid="stTextArea"] textarea {{ min-height: 190px !important; }}
    textarea::placeholder {{ color: var(--muted) !important; opacity: 1 !important; }}

    .stButton > button,
    .stFormSubmitButton > button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stBaseButton-primary"] {{
        width: 100%;
        min-height: 3.5rem !important;
        padding: 0.7rem 1rem !important;
        background: var(--sapphire) !important;
        color: var(--workspace) !important;
        border: 2px solid var(--sapphire) !important;
        border-radius: 12px !important;
        font-size: {min(26, max(18, int(st.session_state.font_size * 0.9)))}px !important;
        font-weight: 700 !important;
        transition: background 0.15s ease, transform 0.15s ease;
    }}

    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stBaseButton-primary"]:hover {{
        background: var(--sapphire-dark) !important;
        border-color: var(--sapphire-dark) !important;
        color: var(--workspace) !important;
        transform: translateY(-1px);
    }}

    .stButton > button *,
    .stFormSubmitButton > button *,
    [data-testid="stFormSubmitButton"] button *,
    [data-testid="stBaseButton-primary"] * {{ color: var(--workspace) !important; }}

    button[data-testid="stBaseButton-primary"] {{
        background: #0A369D !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 3px solid var(--sapphire) !important;
        box-shadow: 0 3px 0 var(--sapphire-dark) !important;
    }}

    button[data-testid="stBaseButton-primary"] *,
    button[data-testid="stBaseButton-primary"] span {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    button[data-testid="stBaseButton-primary"]:hover {{
        background: #0B2F78 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    .st-key-read_assessment_aloud button {{
        background: #0A369D !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 3px solid var(--sapphire) !important;
        box-shadow: 0 3px 0 var(--sapphire-dark) !important;
    }}

    .st-key-read_assessment_aloud button *,
    .st-key-read_assessment_aloud button span {{
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    .st-key-read_assessment_aloud button:hover {{
        background: #0B2F78 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }}

    .stButton > button:disabled {{
        background: #E2E8F0 !important;
        color: var(--muted) !important;
        border-color: #829AB1 !important;
        cursor: not-allowed !important;
        transform: none !important;
    }}
    .stButton > button:disabled * {{ color: var(--muted) !important; }}

    .st-key-text_size_panel,
    .st-key-speech_speed_panel {{
        height: 100%;
        padding: 1.1rem 1.2rem;
        background: var(--paper);
        border: 2px solid var(--sapphire);
        border-radius: 16px;
    }}

    .st-key-text_size_panel h3,
    .st-key-speech_speed_panel h3 {{ font-size: 24px !important; }}

    .st-key-text_size_panel [data-testid="stMarkdownContainer"],
    .st-key-speech_speed_panel [data-testid="stMarkdownContainer"] {{
        font-size: 18px !important;
    }}
    .st-key-text_size_panel p,
    .st-key-speech_speed_panel p {{ font-size: 18px !important; }}

    .st-key-text_size_panel .stButton > button,
    .st-key-speech_speed_panel .stButton > button {{ font-size: 17px !important; }}

    .st-key-text_size_panel [data-testid="stCaptionContainer"] *,
    .st-key-speech_speed_panel [data-testid="stCaptionContainer"] * {{
        font-size: 16px !important;
    }}

    [data-testid="stAlert"] {{
        color: var(--ink) !important;
        background: var(--amber-wash) !important;
        border: 2px solid var(--sapphire) !important;
        border-left: 8px solid var(--amber) !important;
        border-radius: 12px !important;
        padding: 1rem 1.1rem !important;
    }}

    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {{
        color: var(--ink) !important;
        font-size: {max(18, int(st.session_state.font_size * 0.85))}px !important;
        line-height: 1.55 !important;
    }}

    [data-testid="stMetric"] {{
        background: var(--paper) !important;
        border: 2px solid var(--sapphire) !important;
        border-radius: 16px !important;
        padding: 1.1rem 1.3rem !important;
    }}

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {{
        color: var(--muted) !important;
        font-size: {max(17, int(st.session_state.font_size * 0.8))}px !important;
    }}

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {{
        color: var(--sapphire) !important;
        font-size: {min(50, int(st.session_state.font_size * 1.6))}px !important;
        font-weight: 750 !important;
    }}

    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] * {{
        color: var(--ink) !important;
        font-size: {max(15, int(st.session_state.font_size * 0.75))}px !important;
    }}

    [class*="st-key-chat_entry_"] {{
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        background: var(--paper);
        border: 2px solid var(--sapphire);
        border-radius: 14px;
    }}

    .st-key-warning_panel,
    .st-key-input_notice,
    .st-key-model_notice,
    .st-key-chat_notice {{
        padding: 1.2rem;
        margin: 1rem 0;
        background: var(--amber-wash);
        border: 2px solid var(--sapphire);
        border-left: 8px solid var(--amber);
        border-radius: 14px;
    }}

    .st-key-neutral_panel {{
        padding: 1rem 1.2rem;
        margin: 1rem 0;
        background: var(--paper);
        border: 2px solid var(--sapphire);
        border-radius: 14px;
    }}

    :focus-visible {{
        outline: 4px solid var(--sapphire) !important;
        outline-offset: 3px !important;
    }}

    a {{ color: var(--sapphire) !important; text-decoration: underline !important; }}
    hr {{ border-color: #9FB3C8 !important; }}

    @media (max-width: 720px) {{
        [data-testid="stMainBlockContainer"] {{
            margin: 0.5rem auto 1rem;
            padding: 1.25rem !important;
            border-radius: 0;
        }}
    }}
    </style>
    """
)


st.session_state.scanned_text = st.text_area(
    "Step 1: Paste the message you want to check",
    value=st.session_state.scanned_text,
    placeholder="Paste a text message, email, or website notification here.",
    height="content",
    help=(
        "Paste the complete message, including its wording and links. "
        "Remove passwords, sign-in codes, account numbers, and other private details first."
    ),
)

if st.button(
    "Scan message for warning signs",
    type="primary",
    help=(
        "Step 2: Select this button. ScamShield checks the message and shows "
        "a model estimate plus any warning signs it finds."
    ),
):
    message_text = st.session_state.scanned_text.strip()

    if not message_text:
        with st.container(key="input_notice"):
            st.markdown("**Please paste or type a message before scanning.**")
    else:
        flags, score, verdict, model_available = analyze_message(message_text)
        st.session_state.current_flags = flags
        st.session_state.scam_score = score
        st.session_state.model_available = model_available
        st.session_state.analysis_verdict = verdict
        st.session_state.has_analyzed = True
        st.session_state.chat_history = []


if st.session_state.has_analyzed:
    st.markdown("## Scan results")

    if st.session_state.model_available:
        st.metric(
            label="Model scam estimate",
            value=f"{st.session_state.scam_score * 100:.0f}%",
            delta="An estimate, not a guarantee",
            delta_color="off",
        )
        st.caption(
            "The model can make mistakes. This score does not prove a message "
            "is safe or fraudulent."
        )
    else:
        with st.container(key="model_notice"):
            st.markdown(
                "**The trained model is unavailable.** These results show only "
                "the warning signs that matched."
            )

    st.markdown(f"**Assessment:** {st.session_state.analysis_verdict}")

    if st.session_state.current_flags:
        with st.container(key="warning_panel"):
            st.markdown("### Please review these warning signs")
            for flag in st.session_state.current_flags:
                st.markdown(f"- {flag}")
            st.markdown(
                "Pause before clicking a link, sharing information, or sending money."
            )
    else:
        with st.container(key="neutral_panel"):
            st.markdown("### No rule-based warning signs matched")
            st.markdown(
                "The model can still identify a message as suspicious. "
                "No matches do not prove a message is safe."
            )

    st.markdown("## Ask ScamShield a question")
    st.markdown(
        "Ask ScamShield what a warning sign means or how to verify a request safely."
    )
    st.caption(
        "When you ask Gemini, the message and your question are sent to Google "
        "to prepare a response. Do not include passwords, sign-in codes, or account numbers."
    )

    for index, message in enumerate(st.session_state.chat_history):
        with st.container(key=f"chat_entry_{index}"):
            label = "Your question" if message["role"] == "user" else "ScamShield guidance"
            st.markdown(f"**{label}**")
            st.markdown(message["content"])

    with st.form("question_form", clear_on_submit=True):
        question = st.text_area(
            "Your question for ScamShield",
            placeholder="For example: How can I check whether this request is real?",
            height="content",
            help=(
                "Ask one question about the message or a warning sign. "
                "Do not include private information."
            ),
        )
        question_submitted = st.form_submit_button("Send question to ScamShield")

    if question_submitted:
        if not question.strip():
            with st.container(key="chat_notice"):
                st.markdown("**Type a question before selecting Send question.**")
        else:
            st.session_state.chat_history.append(
                {"role": "user", "content": question.strip()}
            )

            with st.spinner("Preparing a plain-language answer..."):
                answer = get_chatbot_response(
                    user_query=question.strip(),
                    checked_message=st.session_state.scanned_text,
                    text_analysis_flags=st.session_state.current_flags,
                    scam_probability=st.session_state.scam_score,
                )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )
            st.rerun()

    st.markdown("## Listen to your results")
    st.markdown(
        "Select the button to hear the assessment. Set the reading speed "
        "using the controls at the top of the page."
    )

    if st.button(
        "Read the assessment aloud",
        key="read_assessment_aloud",
        help="Hear the assessment and any warning signs at your selected reading speed.",
    ):
        speech_text = f"Scan complete. Assessment: {st.session_state.analysis_verdict}. "
        if st.session_state.current_flags:
            speech_text += (
                "Warning signs found include: "
                + ", ".join(st.session_state.current_flags)
            )

        safe_speech_text = json.dumps(speech_text).replace("<", "\\u003c")
        speech_speed = st.session_state.speech_speed

        components.html(
            f"""
            <script>
                const message = new SpeechSynthesisUtterance({safe_speech_text});
                message.rate = {speech_speed};
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(message);
            </script>
            """,
            height=0,
            width=0,
        )

    st.markdown("### Ready to review a different message?")
    st.caption("This clears the current message, results, and question history.")
    if st.button("Check another message", key="check_another_message"):
        st.session_state.scanned_text = ""
        st.session_state.current_flags = []
        st.session_state.scam_score = None
        st.session_state.model_available = False
        st.session_state.analysis_verdict = ""
        st.session_state.has_analyzed = False
        st.session_state.chat_history = []
        st.rerun()
else:
    with st.container(key="neutral_panel"):
        st.markdown("### Ready when you are")
        st.markdown(
            "Paste a message above, then select Scan message for warning signs."
        )
