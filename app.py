import streamlit as st
import pandas as pd
import re
import sqlite3
from thefuzz import process
from collections import Counter
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(
    page_title="Football Name Normalizer",
    layout="centered"
)

st.title("⚽ Football Name Normalizer (Myanmar → English)")

# ================= DATABASE =================
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    phone TEXT,
    teams TEXT,
    confidences TEXT,
    comments TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS aliases (
    official TEXT,
    alias TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS alias_pending (
    raw_text TEXT,
    created_at TEXT
)
""")

conn.commit()

# ================= CONSTANTS =================
STANDARD_TEAMS = [
    "Arsenal","Aston Villa","Barcelona","Brighton","Chelsea",
    "Everton","Liverpool","Manchester City","Manchester United",
    "Newcastle United","Real Madrid","Tottenham Hotspur",
    "Inter Milan","AC Milan","Juventus","Napoli","West Ham"
]

phone_pattern = re.compile(r"(09\d{7,9}|959\d{7,9})")

# ================= HELPERS =================
def normalize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def load_alias_map():
    df = pd.read_sql("SELECT * FROM aliases", conn)
    amap = {}
    for _, r in df.iterrows():
        amap.setdefault(r["official"], []).append(r["alias"])
    return amap

def save_pending_alias(text):
    if len(text) < 2:
        return
    c.execute(
        "SELECT 1 FROM alias_pending WHERE raw_text=?",
        (text,)
    )
    if not c.fetchone():
        c.execute(
            "INSERT INTO alias_pending VALUES (?,?)",
            (text, datetime.now().isoformat())
        )
        conn.commit()

def extract_teams_with_confidence(text, alias_map):
    text_norm = normalize(text)
    found = []

    # 1️⃣ Alias exact match
    for official, aliases in alias_map.items():
        for a in aliases:
            if normalize(a) in text_norm:
                found.append({
                    "team": official,
                    "confidence": 1.00
                })
                break

    # 2️⃣ Direct English name
    for team in STANDARD_TEAMS:
        if team.lower() in text_norm and team not in [f["team"] for f in found]:
            found.append({
                "team": team,
                "confidence": 0.95
            })

    # 3️⃣ Fuzzy fallback
    for team in STANDARD_TEAMS:
        if team in [f["team"] for f in found]:
            continue
        match, score = process.extractOne(text_norm, [team.lower()])
        if score >= 85:
            found.append({
                "team": team,
                "confidence": round(score / 100, 2)
            })

    return found

# ================= UI TABS =================
tab1, tab2, tab3, tab4 = st.tabs([
    "📂 Upload",
    "📊 Stats",
    "🗄 Data",
    "🛠 Admin"
])

# ================= TAB 1: UPLOAD =================
with tab1:
    uploaded_file = st.file_uploader("Upload .txt chat file", type=["txt"])

    if uploaded_file:
        alias_map = load_alias_map()

        content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        lines = content.splitlines()

        parsed_users = []
        current = None
        user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            um = user_pattern.match(line)
            if um:
                if current:
                    parsed_users.append(current)
                current = {
                    "name": um.group(1),
                    "phone": "-",
                    "teams": [],
                    "conf": [],
                    "comments": []
                }
                continue

            if current:
                ph = phone_pattern.search(line)
                if ph:
                    current["phone"] = ph.group()
                    continue

                clean = re.sub(r'^\d+[\.\)]*', '', line)
                found = extract_teams_with_confidence(clean, alias_map)

                if found:
                    for f in found:
                        if f["team"] not in current["teams"]:
                            current["teams"].append(f["team"])
                            current["conf"].append(f["confidence"])
                else:
                    current["comments"].append(clean)
                    save_pending_alias(clean)

        if current:
            parsed_users.append(current)

        for u in parsed_users:
            c.execute(
                "INSERT INTO users VALUES (?,?,?,?,?)",
                (
                    u["name"],
                    u["phone"],
                    ", ".join(u["teams"]),
                    ", ".join(str(x) for x in u["conf"]),
                    ", ".join(u["comments"])
                )
            )
        conn.commit()

        st.success(f"✅ {len(parsed_users)} users saved")

# ================= TAB 2: STATS =================
with tab2:
    df = pd.read_sql("SELECT * FROM users", conn)
    if not df.empty:
        all_teams = []
        for t in df["teams"]:
            all_teams += [x.strip() for x in t.split(",") if x]

        counter = Counter(all_teams)
        chart_df = pd.DataFrame(counter.items(), columns=["Team","Count"]).sort_values("Count")

        st.metric("👥 Total Users", len(df))
        st.metric("📞 Users with Phone", df[df["phone"] != "-"].shape[0])

        st.bar_chart(chart_df.set_index("Team"))

# ================= TAB 3: DATA =================
with tab3:
    df = pd.read_sql("SELECT * FROM users", conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Download CSV",
            csv,
            "football_data.csv",
            "text/csv"
        )

# ================= TAB 4: ADMIN =================
with tab4:
    st.subheader("🛠 Alias Admin Panel")

    pending = pd.read_sql("SELECT * FROM alias_pending", conn)
    if pending.empty:
        st.info("No pending aliases 🎉")
    else:
        for _, r in pending.iterrows():
            col1, col2, col3 = st.columns([3,3,1])
            with col1:
                st.text(r["raw_text"])
            with col2:
                team = st.selectbox(
                    "Assign team",
                    STANDARD_TEAMS,
                    key=r["raw_text"]
                )
            with col3:
                if st.button("Save", key=f"save_{r['raw_text']}"):
                    c.execute(
                        "INSERT INTO aliases VALUES (?,?)",
                        (team, r["raw_text"])
                    )
                    c.execute(
                        "DELETE FROM alias_pending WHERE raw_text=?",
                        (r["raw_text"],)
                    )
                    conn.commit()
                    st.rerun()
