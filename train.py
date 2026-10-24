import os

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def master_dataset():
    all_combined_records = []
    target_files = [
        "CEAS_08.csv", "Enron.csv", "Ling.csv", "my_examples.csv", "Nazario.csv",
        "Nigerian_Fraud.csv", "phishing_email.csv", "spam.csv", "SpamAssasin.csv",
    ]
    text_keywords = ["text", "body", "email text", "v2", "sms", "content", "mail"]
    label_keywords = ["label", "type", "email type", "class", "v1", "status", "target"]

    for filename in target_files:
        filepath = os.path.join("data", filename)
        if not os.path.exists(filepath):
            continue

        try:
            df = pd.read_csv(filepath, encoding='utf-8', encoding_errors='ignore', on_bad_lines='skip')
            txt_col, lbl_col = None, None
            for col in df.columns:
                if str(col).lower().strip() in text_keywords:
                    txt_col = col
                    break
            for col in df.columns:
                if str(col).lower().strip() in label_keywords:
                    lbl_col = col
                    break

            if txt_col and lbl_col:
                count = 0
                for idx, row in df.iterrows():
                    raw_text = str(row[txt_col]).strip()
                    raw_label = str(row[lbl_col]).lower().strip()

                    if not raw_text or raw_text.lower() == "nan":
                        continue
                    if raw_label in ["1", "1.0", "phishing email", "spam", "phishing", "fraud", "true"]:
                        binary_label = 1
                    elif raw_label in ["0", "0.0", "safe email", "ham", "legit", "false"]:
                        binary_label = 0
                    else:
                        try:
                            binary_label = 1 if float(raw_label) >= 1.0 else 0
                        except:
                            continue

                    all_combined_records.append({'text_content': raw_text, 'scam_label': binary_label})
                    count += 1
        except Exception:
            continue


    master_unified_df = pd.DataFrame(all_combined_records).dropna().drop_duplicates()
    master_unified_df.to_csv("data/master_unified_dataset.csv", index=False)

    vectorizer = TfidfVectorizer(max_features=12000, stop_words='english', ngram_range=(1, 2))
    X = vectorizer.fit_transform(master_unified_df['text_content'])
    y = master_unified_df['scam_label'].values

    model = LogisticRegression(C=1.2, solver='lbfgs', max_iter=600, class_weight='balanced')
    model.fit(X, y)

    joblib.dump(model, "model.joblib")
    joblib.dump(vectorizer, "vectorizer.joblib")


if __name__ == "__main__":
    master_dataset()