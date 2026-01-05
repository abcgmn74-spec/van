import streamlit as st
import re

st.set_page_config(page_title="Telegram Prediction Analyzer", layout="wide")
st.title("⚽ Telegram Prediction Analyzer")

# =============================
# TEAM ALIAS (Myanmar -> English)
# =============================
TEAM_ALIAS = {
    "Manchester United": ["မန်ယူ", "man united", "man u", "manutd"],
    "Arsenal": ["အာဆင်နယ်", "arsenal"],
    "Liverpool": ["လီဗာပူး", "liverpool"],
    "Aston Villa": ["ဗီလာ", "အက်စတွန်ဗီလာ", "villa", "aston villa"],
    "Barcelona": ["ဘာစီ", "ဘာစီလိုနာ", "barcelona"],
    "Chelsea": ["ချဲလ်ဆီး", "chelsea"],
}

def normalize_team(text):
    text = text.lower()
    for eng, aliases in TEAM_ALIAS.items():
        for a in aliases:
            if a in text:
                return eng
    return None

def extract_phone(text):
    return re.findall(r'(09\d{7,9}|95\d{8,12})', text)

# =============================
# FILE UPLOAD
# =============================
uploaded = st.file_uploader("📄 Upload TXT file", type="txt")

if uploaded:
    raw = uploaded.read().decode("utf-8", errors="ignore")
    blocks = raw.split("\n\n")

    rows = []
    no = 1

    # -------- Parse ----------
    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue

        user = lines[0].split(",")[0]

        teams = []
        phones = []

        for line in lines[1:]:
            phone = extract_phone(line)
            if phone:
                phones.extend(phone)
            else:
                team = normalize_team(line)
                if team and team not in teams:
                    teams.append(team)

        if teams:
            rows.append({
                "No": no,
                "User": user,
                "Teams": teams,
                "TeamsText": ", ".join(teams),
                "Phone": ", ".join(phones)
            })
            no += 1

    # -------- UI ----------
    all_teams = sorted({t for r in rows for t in r["Teams"]})

    selected_teams = st.multiselect(
        "🔍 Select team(s)",
        all_teams
    )

    logic = st.radio(
        "Filter logic",
        ["OR (any selected team)", "AND (all selected teams)"]
    )

    # -------- Filter ----------
    if selected_teams:
        if logic.startswith("AND"):
            filtered = [
                r for r in rows
                if all(t in r["Teams"] for t in selected_teams)
            ]
        else:
            filtered = [
                r for r in rows
                if any(t in r["Teams"] for t in selected_teams)
            ]
    else:
        filtered = rows

    # -------- Display ----------
    st.subheader(f"📊 Result (Total: {len(filtered)})")

    st.dataframe(
        [
            {
                "No": r["No"],
                "User": r["User"],
                "Teams": r["TeamsText"],
                "Phone": r["Phone"]
            }
            for r in filtered
        ],
        use_container_width=True
    )
