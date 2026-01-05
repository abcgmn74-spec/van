import streamlit as st
import pandas as pd
import re
from thefuzz import process

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Football Data Extractor",
    layout="wide"
)

st.title("⚽ Football Data Extractor (No AI Version)")

# ---------------- DATA ----------------
STANDARD_TEAMS = [
    "Arsenal", "Aston Villa", "Barcelona", "Brighton", "Chelsea",
    "Everton", "Liverpool", "Manchester City", "Manchester United",
    "Newcastle United", "Real Madrid", "Sevilla", "Tottenham Hotspur",
    "Villarreal", "Atletico Madrid", "Inter Milan", "AC Milan",
    "Juventus", "Napoli", "West Ham"
]

TEAM_MAP = {
    "မန်စီး": "Manchester City",
    "မန်ယူ": "Manchester United",
    "လီဗာပူး": "Liverpool",
    "အာဆင်နယ်": "Arsenal",
    "ဘာစီလိုနာ": "Barcelona",
    "ရီးရဲလ်": "Real Madrid",
    "နယူး": "Newcastle United",
    "ဘရိုက်တန်": "Brighton",
    "ဗီလာ": "Aston Villa",
    "စပါး": "Tottenham Hotspur",
    "ဝက်ဟမ်း": "West Ham"
}

phone_pattern = re.compile(r"(09\d{7,9}|959\d{7,9})")

# ---------------- TEAM EXTRACTOR ----------------
def extract_team(text):
    # 1️⃣ Myanmar dictionary
    for k, v in TEAM_MAP.items():
        if k in text:
            return v

    # 2️⃣ Direct English name match
    for team in STANDARD_TEAMS:
        if team.lower() in text.lower():
            return team

    # 3️⃣ Fuzzy match (fallback)
    if len(text) < 40:
        match, score = process.extractOne(text, STANDARD_TEAMS)
        if score > 85:
            return match

    return None

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("📂 Upload .txt chat file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    lines = content.splitlines()

    parsed_data = []
    current_user = None

    user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}')

    with st.spinner("🔍 Data ကို ခွဲခြားနေပါသည်..."):
        for line in lines:
            line = line.strip()
            if not line:
                continue

            user_match = user_pattern.match(line)
            if user_match:
                if current_user:
                    parsed_data.append(current_user)
                current_user = {
                    "Name": user_match.group(1),
                    "Phone": "-",
                    "Teams": set(),
                    "Comments": []
                }
                continue

            if current_user:
                phone_match = phone_pattern.search(line)
                if phone_match:
                    current_user["Phone"] = phone_match.group()
                    continue

                clean_line = re.sub(r'^\d+[\s\.\)]*', '', line)
                if clean_line and clean_line != current_user["Name"]:
                    team = extract_team(clean_line)
                    if team:
                        current_user["Teams"].add(team)
                    else:
                        current_user["Comments"].append(clean_line)

    if current_user:
        parsed_data.append(current_user)

    # ---------------- FILTER ----------------
    st.sidebar.header("🔎 Filter")
    selected_teams = st.sidebar.multiselect(
        "အသင်းအလိုက် စစ်ထုတ်ရန်",
        sorted(STANDARD_TEAMS)
    )

    final_rows = []
    for u in parsed_data:
        if selected_teams and not any(t in u["Teams"] for t in selected_teams):
            continue

        final_rows.append({
            "User Name": u["Name"],
            "Phone Number": u["Phone"],
            "Football Teams": ", ".join(sorted(u["Teams"])),
            "Other Comments": ", ".join(u["Comments"])
        })

    if final_rows:
        df = pd.DataFrame(final_rows)
        st.success(f"✅ တွေ့ရှိသူစုစုပေါင်း: {len(df)} ဦး")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 CSV Download",
            csv,
            "football_data.csv",
            "text/csv"
        )
