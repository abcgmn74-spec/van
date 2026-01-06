import streamlit as st
import pandas as pd
import re
import json
import os
import tempfile
from difflib import get_close_matches
from collections import Counter

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Telegram TXT Parser", page_icon="📄", layout="wide")
st.title("📄 Telegram TXT Parser (Username / Team / User Acc)")

uploaded_file = st.file_uploader("TXT file တင်ပါ", type=["txt"])

# =================================================
# PERSISTENT LEARNING STORAGE (ALWAYS LOAD)
# =================================================
LEARN_FILE = "team_learning.json"

def load_mapping():
    if os.path.exists(LEARN_FILE):
        with open(LEARN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def atomic_save_mapping(data: dict):
    # crash-safe save
    d = os.path.dirname(LEARN_FILE) or "."
    with tempfile.NamedTemporaryFile("w", delete=False, dir=d, encoding="utf-8") as tf:
        json.dump(data, tf, ensure_ascii=False, indent=2)
        temp_name = tf.name
    os.replace(temp_name, LEARN_FILE)

LEARNED_MAP = load_mapping()   # 🔒 always load on start

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
    # 1️⃣ admin learned (always preferred)
    if raw_team in LEARNED_MAP:
        return LEARNED_MAP[raw_team], False

    # 2️⃣ auto fuzzy (high confidence only)
    match = get_close_matches(raw_team, STANDARD_TEAMS, n=1, cutoff=0.85)
    if match:
        return match[0], False

    # 3️⃣ unknown
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
                team_raw = clean_team(line)
                if not team_raw:
                    continue
                std, is_unknown = normalize_team(team_raw)
                teams_raw.append(team_raw)
                teams_std.append(std)
                if is_unknown:
                    unknown_list.append(team_raw)

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
    # ADMIN ROLL – PERSISTENT (STATEFUL MULTI-SELECT)
    # =================================================
    st.subheader("🔴 Admin Roll – Unknown Teams (Persistent Mapping)")

    if unknown_list:
        counter = Counter(unknown_list)

        search_text = st.text_input("🔍 Search unknown team", key="unknown_search")
        sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)

        if search_text:
            sorted_items = [(n,c) for n,c in sorted_items if search_text.lower() in n.lower()]

        options = [f"{name} ({cnt})" for name, cnt in sorted_items]

        if "selected_unknowns" not in st.session_state:
            st.session_state.selected_unknowns = []

        selected_items = st.multiselect(
            "Unknown Teams (RAW)",
            options,
            default=[x for x in st.session_state.selected_unknowns if x in options],
            key="unknown_multiselect"
        )
        st.session_state.selected_unknowns = selected_items

        correct_team = st.selectbox("Correct Standard Team", STANDARD_TEAMS)

        if st.button("💾 Apply & Save Permanently"):
            if not st.session_state.selected_unknowns:
                st.warning("အနည်းဆုံး ၁ ခုရွေးပါ")
            else:
                for item in st.session_state.selected_unknowns:
                    raw_name = item.rsplit("(", 1)[0].strip()
                    LEARNED_MAP[raw_name] = correct_team

                atomic_save_mapping(LEARNED_MAP)   # 🔒 ALWAYS SAVE
                st.session_state.selected_unknowns = []

                st.success("✅ Mapping ကို အမြဲတမ်း သိမ်းပြီးပါပြီ")
                st.info("🔄 Refresh / Next upload မှာ auto-apply ဖြစ်ပါမယ်")

    else:
        st.success("Unknown team မရှိပါ 🎉")

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name="telegram_team_parser.csv",
        mime="text/csv"
    )
