import os

import joblib
import streamlit as st
from google import genai
from google.genai import types



@st.cache_resource(show_spinner=False)
def load_scam_model():
    """Load the trained classifier once per Streamlit process."""
    app_folder = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(app_folder, "model.joblib")
    vectorizer_path = os.path.join(app_folder, "vectorizer.joblib")

    if not os.path.isfile(model_path) or not os.path.isfile(vectorizer_path):
        return None, None

    try:
        return joblib.load(model_path), joblib.load(vectorizer_path)
    except Exception:
        return None, None


def analyze_message(text):
    """Return rule clues and the trained model's scam-class score."""
    flags, _, _ = check_manual_rules(text)
    model, vectorizer = load_scam_model()

    if model is None or vectorizer is None:
        return flags, None, "The trained model could not be loaded. This scan only shows matching warning signs.", False

    try:
        message_vector = vectorizer.transform([str(text)])
        probabilities = model.predict_proba(message_vector)[0]
        classes = list(model.classes_)
        scam_index = next(
            index for index, label in enumerate(classes)
            if str(label).strip().lower() in {"1", "1.0", "scam", "spam", "phishing", "fraud"}
        )
        score = float(probabilities[scam_index])
    except Exception:
        return flags, None, "The trained model could not score this message. Review the warning signs below.", False

    if score >= 0.5:
        verdict = "The model found patterns more similar to its scam examples."
    else:
        verdict = "The model found patterns more similar to its legitimate examples."

    return flags, score, verdict, True


def check_manual_rules(text):
    if not text or not str(text).strip():
        return [], 0.0, "No message was provided for review."

    text_lower = str(text).lower()
    flags = []

    if any(
        phrase in text_lower
        for phrase in [
            "gift card",
            "itunes",
            "target card",
            "wire transfer",
            "crypto",
            "zelle",
            "moneygram",
        ]
    ):
        flags.append(
            "Requests an unusual payment method, such as gift cards, "
            "a wire transfer, or cryptocurrency."
        )

    if any(
        phrase in text_lower
        for phrase in [
            "urgent",
            "immediately",
            "locked",
            "suspended",
            "warrant",
            "arrest",
            "police",
            "jail",
        ]
    ):
        flags.append(
            "Uses urgency or fear to pressure the recipient into acting quickly."
        )

    if any(
        phrase in text_lower
        for phrase in [
            "don't tell",
            "keep this secret",
            "secretly",
            "don't call",
            "stay quiet",
        ]
    ):
        flags.append(
            "Encourages the recipient to hide information or keep secrets."
        )

    if any(
        phrase in text_lower
        for phrase in ["bit.ly", "tinyurl.com", "t.co", "rb.gy"]
    ):
        flags.append(
            "Contains a shortened link that hides its full destination."
        )

    mentions_service = any(
        phrase in text_lower
        for phrase in ["medicare", "social security", "irs", "utility", "power bill"]
    )
    requests_account_change = any(
        phrase in text_lower
        for phrase in ["expire", "update", "cancel", "deactivate"]
    )

    if mentions_service and requests_account_change:
        flags.append(
            "May impersonate a government agency or utility and request an account update."
        )

    score = min(len(flags) / 5, 1.0)

    if score >= 0.6:
        verdict = "Several common warning signs were detected."
    elif flags:
        verdict = "Some common warning signs were detected."
    else:
        verdict = (
            "No matching warning signs were detected. "
            "This does not prove the message is safe."
        )

    return flags, score, verdict


def get_chatbot_response(
    user_query,
    checked_message,
    text_analysis_flags,
    scam_probability,
):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            api_key = None

    if not api_key:
        return (
            "The Gemini API key is not configured. "
            "Add GEMINI_API_KEY to your environment or Streamlit secrets."
        )

    threat_flags = (
        ", ".join(text_analysis_flags)
        if text_analysis_flags
        else "No matching warning-sign patterns were found."
    )

    score_description = (
        f"{scam_probability:.0%} (model estimate, not a guarantee)"
        if scam_probability is not None
        else "unavailable"
    )

    system_instruction = (
        "You are ScamShield, a calm and helpful message-safety assistant. "
        "Give clear, concise guidance in plain language. Avoid emojis and jargon. "
        "The trained text model can make mistakes and cannot prove whether a message "
        "is safe or fraudulent. Do not present its score as a definitive probability. "
        "Never ask the user to share passwords, verification codes, or financial details. "
        "When appropriate, suggest contacting an organization using a phone number "
        "or website the user finds independently, such as on a bank card or official bill.\n\n"
        f"Message being reviewed: {checked_message}\n"
        f"Model estimate: {score_description}\n"
        f"Detected warning signs: {threat_flags}"
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )

        if response and response.text:
            return response.text

        return "Gemini did not return a response. Please try again."
    except Exception:
        return (
            "I couldn't connect to Gemini just now. "
            "Please try again in a moment."
        )