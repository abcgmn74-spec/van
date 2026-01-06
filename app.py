import streamlit as st
import pandas as pd
import re
import json
import os
from difflib import get_close_matches

# -------------------------------------------------
# PAGE CONFIG (FULL WIDTH)
# -------------------------------------------------
st.set_page_config(
    page_title="Telegram TXT Parser",
    page_icon="📄",
    layout="wide"   # ✅ FULL WIDTH
)

st.title("📄 Telegram TXT Parser (Username / Team / User Acc)")

uploaded_file = st.file_uploader("TXT file တင်ပါ", type=["txt"])

# -------------------------------------------------
# Persistent learning storage
# -------------------------------------------------
LEARN_FILE = "team_learning.json"
if os.path.exists(LEARN_FILE):
    with open(LEARN_FILE, "r", encoding="utf-8") as f:
        LEARNED_MAP = json.load(f)
else:
    LEARNED_MAP = {}

# -------------------------------------------------
# Standard teams
# -------------------------------------------------
STANDARD_TEAMS = [
    "Real Madrid","Barcelona","Manchester United","Manchester City",
    "Liverpool","Arsenal","Chelsea","Tottenham","Newcastle",
    "Brighton","Aston Villa","Everton","West Ham","Sevilla",
    "Villarreal","Athletic Club","Wolves","Brentford","Leeds",
    "Fulham","Forest","Burnley","Bournemouth"
]

# -------------------------------------------------
# Regex patterns
# -------------------------------------------------
USER_HEADER = re.compile(
    r"^(.+?),\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\]$"
)

PHONE_PATTERN = re.compile(r"(?:\+?959|09)\d{7,12}")
USER_ACC_KEYWORDS = re.compile(r"(ok\s*bet|okbet|slot|shank|bet)", re.I)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def extract_username(line):
    m = USER_HEADER.match(line)
    return m.group(1).strip() if m else None

def is_user_acc(line):
    return bool(PHONE_PATTERN.search(line) or USER_ACC_KEYWORDS.search(line))

def clean_team(line):
    return re.sub(r"^[\d\.\-\)\s]+", "", line).strip()

def normalize_team(raw_team):
    # 1️⃣ admin learned mapping
    if raw_team in LEARNED_MAP:
        return LEARNED_MAP[raw_team], False

    # 2️⃣ fuzzy matching
    match = get_close_matches(raw_team, STANDARD_TEAMS, n=1, cutoff=0.82)
    if match:
        return match[0], False

    # 3️⃣ unknown
    return raw_team, True

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")

    blocks = re.split(
        r"(?=^.+?,\s*\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)\])",
        text,
        flags=re.MULTILINE
    )

    records = []
    unknown_pool = set()

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        username = extract_username(lines[0])
        if not username:
            continue

        teams_raw = []
        teams_std = []
        user_acc = []

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
                    unknown_pool.add(team_raw)

        records.append({
            "Username": username,
            "Teams (RAW)": ", ".join(dict.fromkeys(teams_raw)),
            "Teams (STANDARD)": ", ".join(dict.fromkeys(teams_std)),
            "User Acc": ", ".join(user_acc)
        })

    df = pd.DataFrame(records)

    st.success(f"✅ Parsed users: {len(df)}")

    # -------------------------------------------------
    # MAIN TABLE (FULL WIDTH)
    # -------------------------------------------------
    st.dataframe(df, use_container_width=True)

    # -------------------------------------------------
    # ADMIN ROLL
    # -------------------------------------------------
   # ---------------- ADMIN ROLL (EXCEL-LIKE MULTI SELECT) ----------------
st.subheader("🔴 Admin Roll – Unknown Teams (Batch Edit)")

if unknown_pool:
    # count unknown frequency
    from collections import Counter
    unknown_list = []
    for t in unknown_pool:
        unknown_list.append(t)

    unknown_counter = Counter(unknown_list)

    # show multiselect with count
    options = [
        f"{name}  ({count})"
        for name, count in unknown_counter.items()
    ]

    selected = st.multiselect(
        "Unknown Teams (RAW) – Excel လို checkbox နဲ့ရွေးပါ",
        options
    )

    correct_team = st.selectbox(
        "Correct Standard Team",
        STANDARD_TEAMS
    )

    if st.button("💾 Apply to Selected"):
        if not selected:
            st.warning("အနည်းဆုံး ၁ ခုရွေးပါ")
        else:
            for item in selected:
                raw_name = item.rsplit("(", 1)[0].strip()
                LEARNED_MAP[raw_name] = correct_team

            with open(LEARN_FILE, "w", encoding="utf-8") as f:
                json.dump(LEARNED_MAP, f, ensure_ascii=False, indent=2)

            st.success(
                f"✅ {len(selected)} team(s) ကို '{correct_team}' အဖြစ် ပြင်ပြီးပါပြီ"
            )
            st.info("🔄 App ကို rerun / refresh လုပ်ပါ")

else:
    st.success("Unknown team မရှိပါ 🎉")

    # -------------------------------------------------
    # EXPORT
    # -------------------------------------------------
    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        file_name="telegram_team_parser.csv",
        mime="text/csv"
    )

