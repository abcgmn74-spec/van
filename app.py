import streamlit as st
import pandas as pd
import re
import json
import os

st.set_page_config(page_title="Team Parser (Raw + Learning)", page_icon="⚽")
st.title("⚽ Football Team Parser (Raw + Learning Architecture)")

UPLOAD_HELP = """
• User ရိုက်ထားတဲ့ team စာလုံးတွေကို **မပြင်ပါ**
• Admin က correct team ကို နောက်ကွယ်မှာ map လုပ်နိုင်ပါတယ်
"""

uploaded_file = st.file_uploader("📄 TXT file တင်ပါ", type=["txt"], help=UPLOAD_HELP)

# -------------------------------------------------
# Persistent learning storage
# -------------------------------------------------
LEARN_FILE = "learning_map.json"
if os.path.exists(LEARN_FILE):
    with open(LEARN_FILE, "r", encoding="utf-8") as f:
        LEARNED_MAP = json.load(f)
else:
    LEARNED_MAP = {}

STANDARD_TEAMS = [
    "Aston Villa", "Barcelona", "Real Madrid", "Arsenal", "Liverpool",
    "Man City", "Man United", "Tottenham", "Brighton", "Newcastle",
    "Sevilla", "Everton", "West Ham", "Villarreal", "Athletic Club",
    "Wolves", "Brentford", "Leeds", "Fulham", "Forest", "Osasuna"
]

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def clean_name(line: str) -> str:
    return re.sub(r",\s*\[.*?\]", "", line).strip()

def extract_phone(text: str) -> str:
    phones = re.findall(r"(?:\+?959|09)\d{7,9}", text)
    return phones[0] if phones else ""

def is_non_team_line(line: str) -> bool:
    return bool(re.search(r"(okbet|slot|phone|bet|\d)", line.lower()))

def extract_raw_teams(lines):
    raw = []
    for line in lines:
        if is_non_team_line(line):
            continue
        # remove numbering like 1. 2)
        clean = re.sub(r"^[\d\W]+", "", line).strip()
        if clean:
            raw.append(clean)
    return raw

def normalize_teams(raw_teams):
    normalized = []
    unknown = []

    for t in raw_teams:
        if t in LEARNED_MAP:
            normalized.append(LEARNED_MAP[t])
        else:
            unknown.append(t)

    return normalized, unknown

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    blocks = content.split("\n\n")

    user_records = []
    unknown_pool = set()

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if len(lines) < 2:
            continue

        name = clean_name(lines[0])
        phone = extract_phone(block)

        raw_teams = extract_raw_teams(lines[1:])
        normalized, unknown = normalize_teams(raw_teams)

        unknown_pool.update(unknown)

        user_records.append({
            "Name": name,
            "Phone": phone,
            "Raw Teams (User Input)": ", ".join(raw_teams),
            "Normalized Teams (System)": ", ".join(normalized)
        })

    df = pd.DataFrame(user_records)

    # -------------------------------------------------
    # USER VIEW
    # -------------------------------------------------
    st.subheader("🟢 User Data (RAW – မပြင်)")
    st.dataframe(
        df[["Name", "Phone", "Raw Teams (User Input)"]],
        use_container_width=True
    )

    # -------------------------------------------------
    # SYSTEM VIEW
    # -------------------------------------------------
    st.subheader("🔵 System View (Learned)")
    st.dataframe(
        df[["Name", "Normalized Teams (System)"]],
        use_container_width=True
    )

    # -------------------------------------------------
    # ADMIN LEARNING ROLL
    # -------------------------------------------------
    st.subheader("🧠 Admin Learning Roll")

    if unknown_pool:
        st.info("အောက်က RAW team တွေကို admin က correct team နဲ့ map လုပ်နိုင်ပါတယ်")

        raw_word = st.selectbox("RAW Team (User Input)", sorted(unknown_pool))
        correct_team = st.selectbox("Correct Team", STANDARD_TEAMS)

        if st.button("💾 Save Learning"):
            LEARNED_MAP[raw_word] = correct_team
            with open(LEARN_FILE, "w", encoding="utf-8") as f:
                json.dump(LEARNED_MAP, f, ensure_ascii=False, indent=2)

            st.success(f"Learned: '{raw_word}' → '{correct_team}'")
            st.info("App ကို rerun လုပ်ပါ (learning အသစ်သုံးမယ်)")
    else:
        st.success("Unknown team မရှိပါ 🎉")

    # -------------------------------------------------
    # EXPORT
    # -------------------------------------------------
    st.download_button(
        "⬇️ Download CSV (Raw + Normalized)",
        df.to_csv(index=False),
        file_name="team_parser_result.csv",
        mime="text/csv"
    )
