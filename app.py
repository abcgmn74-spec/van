import streamlit as st
import pandas as pd
import re
import json
import os

st.set_page_config(page_title="Team Parser (RAW ONLY)", page_icon="⚽")
st.title("⚽ Football Team Parser (RAW User Data Only)")

uploaded_file = st.file_uploader("📄 TXT file တင်ပါ", type=["txt"])

# -------------------------------------------------
# Learning storage (backend only, UI hidden)
# -------------------------------------------------
LEARN_FILE = "learning_map.json"
if os.path.exists(LEARN_FILE):
    with open(LEARN_FILE, "r", encoding="utf-8") as f:
        LEARNED_MAP = json.load(f)
else:
    LEARNED_MAP = {}

STANDARD_TEAMS = [
    "Aston Villa","Barcelona","Real Madrid","Arsenal","Liverpool",
    "Man City","Man United","Tottenham","Brighton","Newcastle",
    "Sevilla","Everton","West Ham","Villarreal","Athletic Club",
    "Wolves","Brentford","Leeds","Fulham","Forest","Osasuna",
    "Chelsea","Burnley","Bournemouth","Sunderland","Celta Vigo"
]

# -------------------------------------------------
# STRICT USER HEADER DETECTOR
# -------------------------------------------------
USER_HEADER_PATTERN = re.compile(
    r"^(.+?),\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\]$"
)

def extract_name(line):
    m = USER_HEADER_PATTERN.match(line)
    return m.group(1).strip() if m else None

def extract_phone(text):
    phones = re.findall(r"(?:\+?959|09)\d{7,12}", text.replace(" ", ""))
    return phones[0] if phones else ""

def is_non_team_line(line):
    return bool(re.search(r"(okbet|slot|bet|\d{5,})", line.lower()))

def extract_raw_teams(lines):
    raw = []
    for line in lines:
        if is_non_team_line(line):
            continue
        clean = re.sub(r"^[\W\d]+", "", line).strip()
        if clean:
            raw.append(clean)
    return raw

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")

    # 🔑 split ONLY by valid user header
    blocks = re.split(
        r"(?=^.+?,\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\])",
        content,
        flags=re.MULTILINE
    )

    records = []

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        name = extract_name(lines[0])
        if not name:
            continue  # ❌ skip emoji / a / b / c messages

        phone = extract_phone(block)
        raw_teams = extract_raw_teams(lines[1:])

        records.append({
            "Name": name,
            "Phone": phone,
            "Raw Teams (User Input)": ", ".join(raw_teams)
        })

    df = pd.DataFrame(records)

    st.success(f"✅ Total users parsed: {len(df)}")

    # ---------------- USER VIEW ONLY ----------------
    st.subheader("🟢 User Data (RAW – TXT အတိုင်း)")
    st.dataframe(df, use_container_width=True)

    # ---------------- EXPORT ----------------
    st.download_button(
        "⬇️ Download CSV (RAW only)",
        df.to_csv(index=False),
        file_name="team_parser_raw_only.csv",
        mime="text/csv"
    )
