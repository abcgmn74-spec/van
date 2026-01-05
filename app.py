import streamlit as st
import pandas as pd
import re
from difflib import get_close_matches

# -------------------------
# TEAM DATABASE
# -------------------------
TEAM_MAP = {
    "manchester united": ["man utd", "manu", "မန်ယူ", "မန်ချက်စတာယူနိုက်တက်"],
    "manchester city": ["man city", "mancity", "မန်စီးတီး"],
    "liverpool": ["liverpool", "liverpol", "လီဗာပူး"],
    "arsenal": ["arsenal", "asenal", "အာဆင်နယ်"],
    "chelsea": ["chelsea", "chelsa", "ချယ်လ်ဆီး"],
}

# -------------------------
# FUNCTIONS
# -------------------------
def normalize_team(text):
    text = text.lower()
    for correct, variants in TEAM_MAP.items():
        for v in variants:
            if v in text:
                return correct

    words = re.findall(r"[a-zA-Z]+", text)
    for w in words:
        match = get_close_matches(w, TEAM_MAP.keys(), cutoff=0.75)
        if match:
            return match[0]

    return None


def extract_username(text):
    m = re.search(r'@[\w\d_]+', text)
    return m.group() if m else None


def extract_phone(text):
    return re.findall(r'(09\d{7,9})', text)


# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Telegram Prediction Analyzer", layout="wide")

st.title("⚽ Telegram Prediction Analyzer")
st.write("TXT file upload လုပ်ပြီး user prediction တွေကို clean & analyze လုပ်ပါ")

uploaded_file = st.file_uploader("📄 Upload TXT file", type=["txt"])

if uploaded_file:
    lines = uploaded_file.read().decode("utf-8").splitlines()

    data = []
    unknown_texts = []
    phones = []

    for line in lines:
        if not line.strip():
            continue

        username = extract_username(line)
        phone = extract_phone(line)
        team = normalize_team(line)

        if phone:
            phones.extend(phone)

        if team:
            data.append({
                "User": username,
                "Team": team,
                "Raw Text": line
            })
        else:
            unknown_texts.append(line)

    df = pd.DataFrame(data)

    # -------------------------
    # MAIN TABLE
    # -------------------------
    st.subheader("✅ Cleaned Predictions")
    st.dataframe(df, use_container_width=True)

    # -------------------------
    # TEAM FILTER
    # -------------------------
    st.subheader("🔍 Filter by Team")
    team_choice = st.selectbox(
        "Choose team",
        sorted(df["Team"].unique()) if not df.empty else []
    )

    if team_choice:
        filtered = df[df["Team"] == team_choice]
        st.write(f"**{team_choice} ကိုခန့်မှန်းထားတဲ့ user များ**")
        st.dataframe(filtered, use_container_width=True)

    # -------------------------
    # UNKNOWN TEXT
    # -------------------------
    st.subheader("❌ Football Team မဟုတ်တဲ့ Text များ")
    st.text_area("Unknown Inputs", "\n".join(unknown_texts), height=200)

    # -------------------------
    # PHONE NUMBERS
    # -------------------------
    st.subheader("📱 Extracted Phone Numbers")
    st.write(list(set(phones)))

    # -------------------------
    # DOWNLOAD
    # -------------------------
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Cleaned CSV",
        csv,
        "clean_predictions.csv",
        "text/csv"
    )

else:
    st.info("⬆️ TXT file တစ်ခု upload လုပ်ပါ")
