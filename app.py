import json

import streamlit as st
import streamlit.components.v1 as components

from rules import analyze_message, get_chatbot_response


st.set_page_config(
    page_title="ScamShield",
    page_icon="scamshield_icon.png",
    layout="centered",
    initial_sidebar_state="expanded",
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





with st.sidebar:
    with st.container(key="font_size_controls"):
        st.markdown("## Make it comfortable to read")
    
        smaller_col, larger_col = st.columns(2)
        with smaller_col:
            if st.button(
                "Smaller text",
                key="smaller_text",
                disabled=st.session_state.font_size <= 18,
            ):
                st.session_state.font_size = max(18, st.session_state.font_size - 2)
    
        with larger_col:
            if st.button(
                "Larger text",
                key="larger_text",
                disabled=st.session_state.font_size >= 34,
            ):
                st.session_state.font_size = min(34, st.session_state.font_size + 2)
    
        st.session_state.font_size = st.slider(
            "Text size",
            min_value=18,
            max_value=34,
            value=st.session_state.font_size,
            step=2,
            help="Adjusts the message, headings, results, and chat text.",
        )
        st.caption(f"Current text size: {st.session_state.font_size}")

    st.session_state.speech_speed = st.slider(
        "Reading speed",
        min_value=0.5,
        max_value=1.5,
        value=st.session_state.speech_speed,
        step=0.1,
    )

    st.markdown("---")
    st.markdown("## How ScamShield works")
    st.caption(
        "Your message is checked an AI which was trained on a dataset of known scams. "
        "If you ask our chatbot a question, it will use the information from the analysis to provide guidance. "
        "Never share passwords or sign-in codes."
    )


st.html(
    f"""
    <style>
    :root {{
        color-scheme: light;
        --ink: #172D43;
        --muted: #43596E;
        --navy: #153C5E;
        --navy-deep: #102F4C;
        --teal: #176F68;
        --gold: #B9782C;
        --line: #D6DFE5;
        --surface: #FFFFFF;
        --page: #F6F4EE;
        --soft: #EAF0F3;
    }}

    html, body, .stApp {{
        background: var(--page) !important;
        color: var(--ink) !important;
        font-family: Arial, sans-serif !important;
    }}

    [data-testid="stHeader"] {{
        background: rgba(246, 244, 238, 0.96) !important;
    }}

    [data-testid="stMainBlockContainer"] {{
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }}

    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div {{
        background: #E9EEF1 !important;
        border-right: 1px solid var(--line);
    }}

    .stApp p,
    .stApp label,
    .stApp li,
    .stApp [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
        color: var(--ink) !important;
        font-size: {st.session_state.font_size}px !important;
        line-height: 1.65 !important;
    }}

    h1, h2, h3, h4 {{
        color: var(--navy) !important;
        font-weight: 750 !important;
        letter-spacing: -0.025em;
    }}

    h1 {{ font-size: {min(52, int(st.session_state.font_size * 1.9))}px !important; margin: 0 0 0.3rem !important; }}
    h2 {{ font-size: {min(38, int(st.session_state.font_size * 1.4))}px !important; }}
    h3 {{ font-size: {min(32, int(st.session_state.font_size * 1.15))}px !important; }}

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] * {{
        color: var(--muted) !important;
        font-size: {max(16, int(st.session_state.font_size * 0.8))}px !important;
        line-height: 1.55 !important;
    }}

    .stTextArea textarea,
    [data-baseweb="textarea"] textarea,
    [data-testid="stChatInput"] textarea {{
        background: var(--surface) !important;
        color: var(--ink) !important;
        border: 2px solid #9BAEBC !important;
        border-radius: 14px !important;
        font-size: {st.session_state.font_size}px !important;
        line-height: 1.6 !important;
        padding: 16px !important;
    }}

    .stTextArea textarea:focus,
    [data-baseweb="textarea"] textarea:focus,
    [data-testid="stChatInput"] textarea:focus {{
        border-color: var(--teal) !important;
        box-shadow: 0 0 0 4px rgba(23, 111, 104, 0.16) !important;
    }}

    textarea::placeholder {{ color: #536A7C !important; opacity: 1 !important; }}

    [data-testid="stTextArea"] label,
    [data-testid="stWidgetLabel"] p {{
        color: var(--ink) !important;
        font-weight: 700 !important;
    }}

    .stButton > button,
    [data-testid="stBaseButton-primary"] {{
        width: 100%;
        min-height: 3.5rem !important;
        padding: 0.65rem 1.3rem !important;
        background: var(--navy) !important;
        color: #FFFFFF !important;
        border: 2px solid var(--navy) !important;
        border-radius: 12px !important;
        font-size: {min(26, max(18, int(st.session_state.font_size * 0.9)))}px !important;
        font-weight: 700 !important;
        transition: background 0.15s ease, transform 0.15s ease;
    }}

    .stButton > button:hover,
    [data-testid="stBaseButton-primary"]:hover {{
        background: var(--navy-deep) !important;
        border-color: var(--navy-deep) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }}

    .stButton > button *,
    [data-testid="stBaseButton-primary"] * {{ color: #FFFFFF !important; }}

    .stButton > button:disabled {{
        background: #DCE3E8 !important;
        color: #405569 !important;
        border-color: #B6C4CE !important;
        cursor: not-allowed !important;
        transform: none !important;
    }}
    .stButton > button:disabled * {{ color: #405569 !important; }}

    .st-key-font_size_controls h2 {{ font-size: 26px !important; }}
    .st-key-font_size_controls label,
    .st-key-font_size_controls [data-testid="stWidgetLabel"] * {{ font-size: 18px !important; }}
    .st-key-font_size_controls .stButton > button {{ font-size: 18px !important; }}
    .st-key-font_size_controls [data-testid="stCaptionContainer"] * {{ font-size: 16px !important; }}

    [data-testid="stAlert"] {{
        background: #EDF3F6 !important;
        border: 1px solid #C6D5DE !important;
        border-radius: 14px !important;
        padding: 1rem 1.1rem !important;
    }}

    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {{
        color: var(--ink) !important;
        font-size: {max(18, int(st.session_state.font_size * 0.85))}px !important;
        line-height: 1.55 !important;
    }}

    [data-testid="stMetric"] {{
        background: var(--surface) !important;
        border: 1px solid var(--line) !important;
        border-left: 6px solid var(--teal) !important;
        border-radius: 16px !important;
        padding: 1.1rem 1.3rem !important;
        box-shadow: 0 5px 18px rgba(21, 38, 59, 0.07);
    }}

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] * {{
        color: var(--muted) !important;
        font-size: {max(17, int(st.session_state.font_size * 0.8))}px !important;
    }}

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {{
        color: var(--navy) !important;
        font-size: {min(50, int(st.session_state.font_size * 1.6))}px !important;
        font-weight: 750 !important;
    }}

    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] * {{ font-size: {max(15, int(st.session_state.font_size * 0.75))}px !important; }}

    [data-testid="stChatMessage"] {{
        background: var(--surface) !important;
        border: 1px solid var(--line) !important;
        border-radius: 14px !important;
        padding: 0.8rem 1rem !important;
        margin-bottom: 0.8rem !important;
    }}

    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {{ color: var(--ink) !important; }}

    [data-testid="stSlider"] *,
    [data-testid="stSlider"] label {{ color: var(--ink) !important; }}

    [data-testid="stSlider"] [role="slider"] {{
        background: var(--teal) !important;
        border-color: var(--teal) !important;
    }}

    a {{ color: #075E8C !important; text-decoration: underline !important; }}
    :focus-visible {{ outline: 3px solid var(--gold) !important; outline-offset: 3px !important; }}
    hr {{ border-color: var(--line) !important; }}

    @media (max-width: 700px) {{
        [data-testid="stMainBlockContainer"] {{ padding: 1.25rem 1rem 3rem; }}
        h1 {{ font-size: {min(48, int(st.session_state.font_size * 1.7))}px !important; }}
    }}
    </style>
    """
)

logo_col, title_col = st.columns([1, 5], vertical_alignment="center")

with logo_col:
    st.image("scamshield_icon.png", width=84)

with title_col:
    st.title("ScamShield")
    st.markdown(
        "A clear, calm way to review a suspicious message."
    )

st.markdown("### Start with a message")
st.markdown(
    "Paste the message as you received it. ScamShield will explain any warning signs it finds."
)
st.session_state.scanned_text = st.text_area(
    "Message to scan",
    value=st.session_state.scanned_text,
    placeholder="Paste a suspicious notification or text message here.",
    height=190,
)
st.caption(
    "Tip: remove personal details before pasting. Never include a password or verification code."
)

if st.button("Scan message", type="primary"):
    message_text = st.session_state.scanned_text.strip()

    if not message_text:
        st.warning("Enter a message before starting the scan.")
    else:
        flags, score, verdict, model_available = analyze_message(message_text)
        st.session_state.current_flags = flags
        st.session_state.scam_score = score
        st.session_state.model_available = model_available
        st.session_state.analysis_verdict = verdict
        st.session_state.has_analyzed = True
        st.session_state.chat_history = []


if st.session_state.has_analyzed:
    st.markdown("---")
    st.markdown("## Your scan results")

    if st.session_state.model_available:
        st.metric(
            label="Trained model scam estimate",
            value=f"{st.session_state.scam_score * 100:.0f}%",
            delta="Model estimate, not a guarantee",
            delta_color="off",
        )
        st.caption(
            "This estimate comes from a text model trained on labeled examples. "
            "It can be wrong and does not prove a message is safe or fraudulent."
        )
    else:
        st.warning(
            "The trained model is unavailable. This result only shows the "
            "rule-based warning signs that matched."
        )

    st.markdown(f"**Assessment:** {st.session_state.analysis_verdict}")

    if st.session_state.current_flags:
        st.error("Warning signs found")
        for flag in st.session_state.current_flags:
            st.markdown(f"- {flag}")
    else:
        st.success(
            "No rule-based warning signs were found. The model can still be wrong; "
            "this does not prove the message is safe."
        )

    st.markdown("---")
    st.markdown("## Ask ScamShield")
    st.caption(
        "Ask a question about the message or what to do next. "
        "Do not share passwords, verification codes, or financial details."
    )

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Type your question here")

    if question:
        st.session_state.chat_history.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Preparing a response..."):
                answer = get_chatbot_response(
                    user_query=question,
                    checked_message=st.session_state.scanned_text,
                    text_analysis_flags=st.session_state.current_flags,
                    scam_probability=st.session_state.scam_score,
                )
            st.markdown(answer)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer}
        )

    st.markdown("---")
    st.markdown("## Listen to the results")

    if st.button("Read results aloud"):
        speech_text = (
            f"Scan complete. Assessment: "
            f"{st.session_state.analysis_verdict}. "
        )

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
else:
    st.info("Paste a message and select “Scan message” to see results and ask questions.")