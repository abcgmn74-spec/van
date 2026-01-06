import streamlit as st
import pandas as pd
import re
import json
import os
import tempfile
from difflib import get_close_matches
from collections import Counter
from datetime import datetime

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Telegram TXT Parser", page_icon="📄", layout="wide")
st.title("📄 Telegram TXT Parser (Team / Other Comment / User Acc)")

uploaded_file = st.file_uploader("TXT file တင်ပါ", type=["txt"])

# =================================================
# FILE PATHS
# =================================================
LEARN_FILE = "team_learning.json"
HISTORY_FILE = "team_learning_history.json"

# =================================================
# LOAD / SAVE
# =================================================
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def atomic_save(path, data):
    d = os.path.dirname(path) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=d, encoding="utf-8") as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        temp = tf.name
    os.replace(temp, path)

LEARNED_MAP = load_json(LEARN_FILE, {})
HISTORY = load_json(HISTORY_FILE, [])

# =================================================
# STANDARD TEAMS
# =================================================
STANDARD_TEAMS = [
    "Real Madrid","Barcelona","Manchester United","Manchester City",
    "Liverpool","Arsenal","Chelsea","Tottenham","Newcastle",
    "Brighton","Aston Villa","Everton","West Ham","Sevilla",
    "Villarreal","Athletic Club","Wolves","Brentford","Leeds",
    "Fulham","Forest","Burnley","Bournemouth","Celta Vigo"
]

# =================================================
# MYANMAR / REAL-WORLD ALIAS
# =================================================
MYANMAR_TEAM_ALIAS = {
    "man city": "Manchester City","man city.": "Manchester City",
    "man united": "Manchester United","man u": "Manchester United",
    "မန်စီးတီး": "Manchester City","စီတီ": "Manchester City",
    "ရီးရဲ": "Real Madrid","ရီးရဲလ်": "Real Madrid",
    "ရီးရဲမက်ဒရစ်": "Real Madrid","ရီရဲ": "Real Madrid",
    "လီပါပူး": "Liverpool","လီပါပူးး": "Liverpool",
    "ဗီလာရီရဲ": "Villarreal","ဗီလာရီးရဲလ်": "Villarreal",
    "နယူး": "Newcastle","နယူကာဆယ်": "Newcastle",
    "ဘရိုက်တန်": "Brighton",
    "aston villa": "Aston Villa",
    "west ham": "West Ham",
    "wolves": "Wolves",
    "athletic club": "Athletic Club",
    "tottenham hotspur": "Tottenham",
    "celta vigo": "Celta Vigo"
}

# =================================================
# REGEX
# =================================================
PHONE_PATTERN = re.compile(r"(?:\+?959|09)\d{7,12}")
USER_ACC_KEYWORDS = re.compile(r"(ok\s*bet|okbet|slot|shank|bet)", re.I)

# =================================================
# HELPERS
# =================================================
def is_user_acc(line):
    return bool(PHONE_PATTERN.search(line) or USER_ACC_KEYWORDS.search(line))

def normalize_raw_token(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"^[^က-႟A-Za-z]+|[^က-႟A-Za-z]+$", "", text)
    return cleaned.strip().lower()

def is_other_comment(token: str) -> bool:
    if not token:
        return True
    if len(token) >= 20:
        return True
    if " " in token and token not in MYANMAR_TEAM_ALIAS:
        return True
    return False

def normalize_team(raw_team):
    raw = normalize_raw_token(raw_team)

    if not raw:
        return raw_team, "other"

    if raw in LEARNED_MAP:
        return LEARNED_MAP[raw], "team"

    if raw in MYANMAR_TEAM_ALIAS:
        return MYANMAR_TEAM_ALIAS[raw], "team"

    match = get_close_matches(raw.title(), STANDARD_TEAMS, n=1, cutoff=0.85)
    if match:
        return match[0], "team"

    if is_other_comment(raw):
        return raw, "other"

    return raw, "unknown"

# =================================================
# MAIN
# =================================================
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    teams, others, unknowns, accounts = [], [], [], []

    for line in lines:
        if is_user_acc(line):
            accounts.append(line)
            continue

        std, kind = normalize_team(line)

        if kind == "team":
            teams.append(std)
        elif kind == "other":
            others.append(line)
        else:
            unknowns.append(line)

    st.success("✅ Parsing completed")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏟 Teams (STANDARD)")
        st.dataframe(pd.DataFrame({"Team": list(dict.fromkeys(teams))}))

        st.subheader("❓ Unknown")
        st.dataframe(pd.DataFrame({"Unknown": list(dict.fromkeys(unknowns))}))

    with col2:
        st.subheader("💬 Other Comment")
        st.dataframe(pd.DataFrame({"Comment": list(dict.fromkeys(others))}))

        st.subheader("👤 User Acc")
        st.dataframe(pd.DataFrame({"Account": list(dict.fromkeys(accounts))}))

    # =================================================
    # ADMIN ROLL
    # =================================================
    if unknowns:
        st.subheader("🔴 Admin Roll – Unknown Teams")
        counter = Counter(unknowns)
        options = [f"{k} ({v})" for k,v in counter.items()]

        selected = st.multiselect("Unknown", options)
        correct_team = st.selectbox("Correct Standard Team", STANDARD_TEAMS)

        if st.button("💾 Apply & Save"):
            for item in selected:
                raw = normalize_raw_token(item.rsplit("(",1)[0])
                LEARNED_MAP[raw] = correct_team

            atomic_save(LEARN_FILE, LEARNED_MAP)
            st.success("✅ Mapping saved permanently")
