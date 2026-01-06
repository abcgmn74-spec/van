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
st.title("📄 Telegram TXT Parser (Username / Team / User Acc)")

uploaded_file = st.file_uploader("TXT file တင်ပါ", type=["txt"])

# =================================================
# FILE PATHS
# =================================================
LEARN_FILE = "team_learning.json"
HISTORY_FILE = "team_learning_history.json"

# =================================================
# LOAD / SAVE HELPERS
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
    "Fulham","Forest","Burnley","Bournemouth"
]

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

def clean_team(line):
    return re.sub(r"^[\d\.\-\)\s]+", "", line).strip()

def normalize_team(raw_team):
    if raw_team in LEARNED_MAP:
        return LEARNED_MAP[raw_team], False

    match = get_close_matches(raw_team, STANDARD_TEAMS, n=1, cutoff=0.85)
    if match:
        return match[0], False

    return raw_team, True

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

        teams_raw, teams_std, user_acc = [], [], []

        for line in lines[1:]:
            if is_user_acc(line):
                user_acc.append(line)
            else:
                raw = clean_team(line)
                if not raw:
                    continue
                std, unk = normalize_team(raw)
                teams_raw.append(raw)
                teams_std.append(std)
                if unk:
                    unknown_list.append(raw)

        records.append({
            "Username": username,
            "Teams (RAW)": ", ".join(dict.fromkeys(teams_raw)),
            "Teams (STANDARD)": ", ".join(dict.fromkeys(teams_std)),
            "User Acc": ", ".join(user_acc)
        })

    df = pd.DataFrame(records)
    st.success(f"✅ Parsed users: {len(df)}")
    st.dataframe(df, use_container_width=True)

    # =================================================
    # ADMIN ROLL – APPLY MAPPING (WITH HISTORY)
    # =================================================
    st.subheader("🔴 Admin Roll – Apply Mapping")

    if unknown_list:
        counter = Counter(unknown_list)
        options = [f"{k} ({v})" for k,v in counter.items()]

        selected = st.multiselect("Unknown Teams", options)
        correct_team = st.selectbox("Correct Standard Team", STANDARD_TEAMS)

        if st.button("💾 Apply & Save"):
            raw_items = []
            for item in selected:
                raw = item.rsplit("(",1)[0].strip()
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

            st.success("✅ Mapping saved with history")

    # =================================================
    # ADMIN HISTORY + RESTORE
    # =================================================
    st.subheader("🕒 Mapping History (Restore)")

    if HISTORY:
        labels = [
            f"{h['time']} | {len(h['raw_items'])} items → {h['mapped_to']}"
            for h in HISTORY
        ]

        idx = st.selectbox("History ရွေးပါ", range(len(labels)),
                           format_func=lambda i: labels[i])

        if st.button("↩️ Restore This Mapping"):
            LEARNED_MAP.clear()
            LEARNED_MAP.update(HISTORY[idx]["snapshot"])
            atomic_save(LEARN_FILE, LEARNED_MAP)

            st.success("♻️ Mapping ကို ဒီနေ့ရက်အခြေအနေအတိုင်း Restore လုပ်ပြီးပါပြီ")
            st.info("🔄 Refresh / Next upload မှာ auto-apply ဖြစ်ပါမယ်")
    else:
        st.info("History မရှိသေးပါ")

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name="telegram_team_parser.csv",
        mime="text/csv"
    )

