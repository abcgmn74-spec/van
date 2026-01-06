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
# MYANMAR / REAL-WORLD ALIAS (FROM YOUR DATA)
# =================================================
MYANMAR_TEAM_ALIAS = {
    # Manchester City
    "man city": "Manchester City",
    "man city.": "Manchester City",
    "man city ": "Manchester City",
    "man city,": "Manchester City",
    "မန်စီးတီး": "Manchester City",
    "စီးတီး": "Manchester City",
    "စီတီ": "Manchester City",

    # Manchester United
    "man united": "Manchester United",
    "man u": "Manchester United",
    "man unnited": "Manchester United",
    "မန်ယူ": "Manchester United",

    # Real Madrid
    "ရီးရဲ": "Real Madrid",
    "ရီးရယ်": "Real Madrid",
    "ရီးရဲလ်": "Real Madrid",
    "ရီးရဲမက်ဒရစ်": "Real Madrid",
    "ရီးရဲလ်မက်ဒရစ်": "Real Madrid",
    "ရီရဲ": "Real Madrid",
    "ရီရဲလ်": "Real Madrid",
    "ရီရဲမက်ဒရစ်": "Real Madrid",

    # Liverpool
    "လီပါပူး": "Liverpool",
    "လီပါပူးး": "Liverpool",
    "လီပါဘူး": "Liverpool",
    "လီပါပူလ်း": "Liverpool",

    # Villarreal
    "ဗီလာရီရဲ": "Villarreal",
    "ဗီလာရီးရဲ": "Villarreal",
    "ဗီလာရီးရဲလ်": "Villarreal",
    "ဗီလာရီရဲလ်": "Villarreal",
    "ဗယ်လာရီးရဲလ်": "Villarreal",

    # Newcastle
    "နယူး": "Newcastle",
    "နယူးကာဆယ်": "Newcastle",
    "နယူကာဆယ်": "Newcastle",
    "နယူးကားဆယ်": "Newcastle",

    # Brighton
    "ဘရိုတ်တန်": "Brighton",
    "ဘရိုက်တန်": "Brighton",
    "ဘရုိက်တန်": "Brighton",

    # Aston Villa
    "aston villa": "Aston Villa",
    "aston viIIa": "Aston Villa",
    "ဗီလာ": "Aston Villa",

    # West Ham
    "west ham": "West Ham",
    "ဝက်စ်ဟမ်း": "West Ham",

    # Forest
    "ဖော့ရက်စ်": "Forest",

    # Brentford
    "ဘရက်ဖို့": "Brentford",
    "ဘရက်ဗိုလ်": "Brentford",

    # Sevilla
    "ဆီဗီလာ": "Sevilla",

    # Fulham
    "ဖူဟမ်": "Fulham",

    # Wolves
    "wolves": "Wolves",

    # Athletic Club
    "athletic club": "Athletic Club",

    # Tottenham
    "tottenham hotspur": "Tottenham",
    "စပါး": "Tottenham",

    # Celta Vigo
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
    if re.fullmatch(r"[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){1,2}", token):
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

    teams_std, other_comments, unknown_list, user_acc = [], [], [], []

    for line in lines:
        if is_user_acc(line):
            user_acc.append(line)
            continue

        std, kind = normalize_team(line)

        if kind == "team":
            teams_std.append(std)
        elif kind == "other":
            other_comments.append(line)
        else:
            unknown_list.append(line)

    df = pd.DataFrame({
        "Teams (STANDARD)": list(dict.fromkeys(teams_std)),
        "Other Comment": list(dict.fromkeys(other_comments)),
        "Unknown": list(dict.fromkeys(unknown_list)),
        "User Acc": list(dict.fromkeys(user_acc))
    })

    st.success("✅ Parsing completed")
    st.dataframe(df, use_container_width=True)

    # =================================================
    # ADMIN ROLL – UNKNOWN
    # =================================================
    if unknown_list:
        st.subheader("🔴 Admin Roll – Unknown Teams")
        counter = Counter(unknown_list)
        options = [f"{k} ({v})" for k,v in counter.items()]

        selected = st.multiselect("Unknown", options)
        correct_team = st.selectbox("Correct Standard Team", STANDARD_TEAMS)

        if st.button("💾 Apply & Save"):
            raw_items = []
            for item in selected:
                raw = normalize_raw_token(item.rsplit("(",1)[0])
                LEARNED_MAP[raw] = correct_team
                raw_items.append(raw)

            atomic_save(LEARN_FILE, LEARNED_MAP)

            HISTORY.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "raw_items": raw_items,
                "mapped_to": correct_team,
                "snapshot": LEARNED_MAP.copy()
            })
            atomic_save(HISTORY_FILE, HISTORY)
            st.success("✅ Mapping saved permanently")

    # =================================================
    # HISTORY RESTORE
    # =================================================
    if HISTORY:
        st.subheader("🕒 Mapping History")
        labels = [
            f"{h['time']} | {len(h['raw_items'])} → {h['mapped_to']}"
            for h in HISTORY
        ]
        idx = st.selectbox("Restore point", range(len(labels)),
                           format_func=lambda i: labels[i])
        if st.button("↩️ Restore"):
            LEARNED_MAP.clear()
            LEARNED_MAP.update(HISTORY[idx]["snapshot"])
            atomic_save(LEARN_FILE, LEARNED_MAP)
            st.success("♻️ Mapping restored")

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name="parsed_result.csv",
        mime="text/csv"
    )
