import os
import sys

try:
    import joblib
except ImportError:
    joblib = None


def scan_text_heuristics(message):
    text = str(message).lower()
    warnings = []

    checks = [
        (
            ["bit.ly", "tinyurl.com", "http:", "https:"],
            "The message contains a link. Check its destination carefully before opening it.",
        ),
        (
            ["gift card", "itunes", "bitcoin", "crypto"],
            "The message mentions gift cards or cryptocurrency as a payment method.",
        ),
        (
            ["urgent", "act now", "locked", "verify immediately"],
            "The message uses urgent or alarming language to pressure you.",
        ),
    ]

    for phrases, warning in checks:
        if any(phrase in text for phrase in phrases):
            warnings.append(warning)

    return warnings


def load_model_assets(app_folder):
    if joblib is None:
        return None, None, "The optional joblib package is not installed."

    model_path = os.path.join(app_folder, "model.joblib")
    vectorizer_path = os.path.join(app_folder, "vectorizer.joblib")

    if not os.path.isfile(model_path) or not os.path.isfile(vectorizer_path):
        return None, None, "Model files were not found. Only the message checks will run."

    try:
        model = joblib.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
        return model, vectorizer, None
    except Exception:
        return None, None, "The model files could not be loaded."


def main():
    print("Paste a message to check, then press Enter:")
    message = input().strip()

    if not message:
        print("No message was entered. Please try again.")
        return 1

    warnings = scan_text_heuristics(message)

    print("\nMessage check:")
    if warnings:
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- No matching warning signs were found.")
        print("  This does not prove the message is safe.")

    app_folder = os.path.dirname(os.path.abspath(__file__))
    model, vectorizer, model_note = load_model_assets(app_folder)

    if model_note:
        print(f"\nMachine learning check: {model_note}")
        return 0

    try:
        message_vector = vectorizer.transform([message])
        prediction = model.predict(message_vector)

        print("\nMachine learning result:")
        print(f"- Model prediction: {prediction[0]}")
    except Exception:
        print(
            "\nThe message checks completed, but the machine learning "
            "model could not analyze this message."
        )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
