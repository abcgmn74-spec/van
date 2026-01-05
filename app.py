import streamlit as st
import pandas as pd
import re
import json
import os
from difflib import get_close_matches

st.set_page_config(page_title="TXT Smart Parser (Learning)", page_icon="🧠")

st.title("📄 TXT Parser (Auto-Learn & Unknown Log)")

uploaded_file = st.file_uploader("TXT file တင်ပါ", type=["txt"])

# --------------------------------
# Standard teams
# --------------------------------
STANDARD_TEAMS = [
    "Aston Villa","Barcelona","Real Madrid","Arsenal","Liverpool",
    "Man City","Man United","Tottenham","Brighton","Newcastle",
    "Sevilla","Everton","West Ham","Villarreal","Athletic Club",
    "Wolves","Brentford","Osasuna","Forest","Fulham","Leeds"
]

# --------------------------------
# Base mapping
# --------------------------------
BASE_MAP = {
    "ဗီလာ": "Aston Villa",
    "ဘာစီ": "Barcelona",
    "ဘာစီလိုနာ": "Barcelona",
    "ရီးရဲ": "Real Madrid",
    "အာဆင်နယ်": "Arsenal",
    "လီဗာပူး": "Liverpool",
    "မန်ယူ": "Man United",
    "မန်စီးတီး": "Man City",
    "စပါး": "Tottenham",
    "ဘရိုက်တန်": "Brighton",
    "နယူးကာဆယ်": "Newcastle",
    "ဆီဗီလာ": "Sevilla",
}

# --------------------------------
# Load learned mapping
# --------------------------------
LEARN_FILE = "learned_mapping.json"
if os.path.exists(LEARN_FILE):
    with open(LEARN_FILE, "r", encoding="utf-8") as f:
        LEARNED_MAP = json.load(f)
else:
    LEARNED_MAP = {}

# Merge maps
TEAM_MAP = {**BASE_MAP, **LEARNED_MAP}

# --------------------------------
# Phone extractor
# --------------------------------
def extract_phone(text):
    phones = re.findall(r"(?:\+?959|09)\d{7,9}", text)
    return phones[0] if phones else ""

# --------------------------------
# Detect teams + unknown
# --------------------------------
def detect_teams_and_unknown(text):
    found = set()
    unknown = set()

    # rule-based
    for key, value in TEAM_MAP.items():
        if key.lower() in text.lower():
            found.add(value)

    # word scanning
    words = re.findall(r"[A-Za-z]{4,}", text)
    for word in words:
        match = get_close_matches(word, STANDARD_TEAMS, n=1, cutoff=0.78)
        if match:
            found.add(match[0])
        else:
            if word.lower() not in [k.lower() for k in TEAM_MAP]:
                unknown.add(word)

    return list(found), list(unknown)

# --------------------------------
# MAIN
# --------------------------------
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    blocks = content.split("\n\n")

    records = []
    unknown_words = set()

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        name = lines[0]
        phone = extract_phone(block)
        teams, unknown = detect_teams_and_unknown(block)

        unknown_words.update(unknown)

        records.append({
            "Name": name,
            "Phone": phone,
            "Teams": ", ".join(teams)
        })

    df = pd.DataFrame(records)

    st.subheader("📊 Parsed Result")
    st.dataframe(df, use_container_width=True)

    # ------------------------------
    # UNKNOWN SPELLING SECTION
    # ------------------------------
    st.subheader("⚠️ Unknown Spellings (Auto-Learn)")

    if unknown_words:
        selected_word = st.selectbox(
            "Unknown word ရွေးပါ",
            sorted(list(unknown_words))
        )

        selected_team = st.selectbox(
            "ဘယ် Team နဲ့ map လုပ်မလဲ",
            STANDARD_TEAMS
        )

        if st.button("💾 Learn Mapping"):
            LEARNED_MAP[selected_word] = selected_team
            with open(LEARN_FILE, "w", encoding="utf-8") as f:
                json.dump(LEARNED_MAP, f, ensure_ascii=False, indent=2)

            st.success(f"Learned: {selected_word} → {selected_team}")
            st.info("App ကို rerun လုပ်ပါ (mapping အသစ်သုံးမယ်)")

    else:
        st.success("Unknown spelling မရှိပါ 🎉")

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name="parsed_learning_result.csv",
        mime="text/csv"
    )
