import streamlit as st
import pandas as pd
import re
import json
import os
import tempfile
from difflib import get_close_matches
from collections import Counter
from datetime import datetime

# ================= HF (FREE) =================
from transformers import pipeline

@st.cache_resource
def load_hf_classifier():
    return pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli"
    )

hf_classifier = load_hf_classifier()

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Telegram TXT Parser", page_icon="📄", layout="wide")
st.title("📄 Telegram TXT Parser (Rule-based + HF AI Suggest)")

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
# MYANMAR / REAL-WORLD ALIAS (SAFE)
# =================================================
MYANMAR_TEAM_ALIAS = {
    "man city": "Manchester City",
    "man united": "Manchester United",
    "man u": "Manchester United",
    "မန်စီးတီး": "Manchester City",
    "ရီးရဲ": "Real Madrid",
    "ရီးရဲလ်": "Real Madrid",
    "လီပါပူး": "Liverpool",
    "ဗီလာရီးရဲလ်": "Villarreal",
    "နယူး": "Newcastle",
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
USER_HEADER = re.compile(
    r"^(.+?),\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\]$"
)
PHONE_PATTERN = re.compile(r"(?:\+?959|09)\d{7,12}")
USER_ACC_KEYWORDS = re.compile(r"(ok\s*bet|okbet|slot|shank|bet)", re.I)

# =================================================
# HELPERS
# =================================================
def extract_username(line):
    m = USER_HEADER.match(line)
    return m.group(1).strip() if m else None

def is_user_acc(line):
    return bool(PHONE_PATTERN.search(line) or USER_ACC_KEYWORDS.search(line))

def normalize_raw_token(text: str) -> str:
    cleaned = re.sub(r"^[^က-႟A-Za-z]+|[^က-႟A-Za-z]+$", "", text)
    return cleaned.strip().lower()

# ---------------- HF AI (Suggest / Classify only)
def hf_classify(text: str) -> str:
    labels = ["football team", "person name", "comment"]
    result = hf_classifier(text, labels)
    return result["labels"][0]   # best label only

def hf_team_suggest(text: str) -> str:
    labels = STANDARD_TEAMS
    result = hf_classifier(text, labels)
    return result["labels"][0]

# ---------------- Rule-based decision
def normalize_team(raw_team):
    raw = normalize_raw_token(raw_team)

    # 1️⃣ Admin learned
    if raw in LEARNED_MAP:
        return LEARNED_MAP[raw], "team", "admin"

    # 2️⃣ Myanmar alias
    if raw in MYANMAR_TEAM_ALIAS:
        return MYANMAR_TEAM_ALIAS[raw], "team", "alias"

    # 3️⃣ English fuzzy
    match = get_close_matches(raw.title(), STANDARD_TEAMS, n=1, cutoff=0.85)
    if match:
        return match[0], "team", "fuzzy"

    # 4️⃣ HF AI classify (suggest only)
    ai_type = hf_classify(raw_team)

    if ai_type != "football team":
        return raw_team, "other", "ai"

    # football team but unknown → AI suggest standard
    ai_team = hf_team_suggest(raw_team)
    return raw_team, "unknown", f"ai-suggest:{ai_team}"

# =================================================
# MAIN
# =================================================
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")

    blocks = re.split(
        r"(?=^.+?,\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\])",
        text,
        flags=re.MULTILINE
    )

    records = []
    unknown_list = []

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        username = extract_username(lines[0])
        if not username:
            continue

        teams, others, accounts, ai_notes = [], [], [], []

        for line in lines[1:]:
            if is_user_acc(line):
                accounts.append(line)
                continue

            std, kind, src = normalize_team(line)

            if kind == "team":
                teams.append(std)
            elif kind == "other":
                others.append(line)
            else:
                unknown_list.append(line)
                ai_notes.append(f"{line} → {src}")

        records.append({
            "Username": username,
            "Teams (STANDARD)": ", ".join(dict.fromkeys(teams)),
            "Other Comment": ", ".join(dict.fromkeys(others)),
            "User Acc": ", ".join(dict.fromkeys(accounts)),
            "AI Note": ", ".join(dict.fromkeys(ai_notes))
        })

    df = pd.DataFrame(records)
    st.success(f"✅ Parsed users: {len(df)}")
    st.dataframe(df, use_container_width=True)

    # =================================================
    # ADMIN ROLL – UNKNOWN
    # =================================================
    if unknown_list:
        st.subheader("🔴 Admin Roll – Unknown Teams (AI Suggest shown)")
        counter = Counter(unknown_list)
        options = [f"{k} ({v})" for k,v in counter.items()]

        selected = st.multiselect("Unknown", options)
        correct_team = st.selectbox("Correct Standard Team", STANDARD_TEAMS)

        if st.button("💾 Apply & Save"):
            for item in selected:
                raw = normalize_raw_token(item.rsplit("(",1)[0])
                LEARNED_MAP[raw] = correct_team

            atomic_save(LEARN_FILE, LEARNED_MAP)

            HISTORY.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "items": selected,
                "mapped_to": correct_team,
                "snapshot": LEARNED_MAP.copy()
            })
            atomic_save(HISTORY_FILE, HISTORY)

            st.success("✅ Mapping saved permanently")
