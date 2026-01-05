import streamlit as st
import re

st.title("Telegram Prediction Chart")

uploaded = st.file_uploader("Upload TXT file", type="txt")

# ----------------------------
# TEAM ALIAS (Myanmar -> English)
# ----------------------------
TEAM_ALIAS = {
    "Aston Villa": ["ဗီလာ", "အက်စတွန်ဗီလာ", "အက်တွန်ဗီလာ", "villa", "aston villa"],
    "Manchester City": ["မန်စီးတီး", "မန်းစီးတီး", "man city", "mancity"],
    "Manchester United": ["မန်ယူ", "man united", "man u", "manutd"],
    "Arsenal": ["အာဆင်နယ်", "arsenal"],
    "Liverpool": ["လီဗာပူး", "လီပါပူး", "liverpool"],
    "Barcelona": ["ဘာစီ", "ဘာစီလိုနာ", "barcelona"],
    "Real Madrid": ["ရီးရဲ", "ရီးရဲလ်", "ရီးရဲမက်ဒရစ်", "real madrid"],
    "Tottenham Hotspur": ["စပါး", "spur", "hotspur", "tottenham"],
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

# ----------------------------
# MAIN
# ----------------------------
if uploaded:
    raw = uploaded.read().decode("utf-8")
    blocks = raw.split("\n\n")

    rows = []
    no = 1

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

        if teams or phones:
            rows.append({
                "No": no,
                "User": user,
                "Teams": ", ".join(teams),
                "Phone": ", ".join(phones)
            })
            no += 1

    st.subheader(f"Result Table (Total: {len(rows)})")
    st.dataframe(rows, use_container_width=True)
