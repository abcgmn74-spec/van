import streamlit as st
import re

st.set_page_config(page_title="Telegram Prediction Analyzer", layout="wide")
st.title("⚽ Telegram Prediction Analyzer")

# =====================================
# TEAM ALIAS (Myanmar / Typo → English)
# =====================================
TEAM_ALIAS = {
    "Aston Villa": ["ဗီလာ", "အက်စတွန်ဗီလာ", "အက်တွန်ဗီလာ", "villa", "aston villa", "astonvilla"],
    "Manchester City": ["မန်စီးတီး", "မန်းစီးတီး", "မန်စီးတီ", "man city", "mancity"],
    "Manchester United": ["မန်ယူ", "man united", "man u", "manutd", "manunited"],
    "Arsenal": ["အာဆင်နယ်", "arsenal", "aresnal"],
    "Liverpool": ["လီဗာပူး", "လီပါပူး", "လီဗာပူးလ်", "liverpool"],
    "Barcelona": ["ဘာစီ", "ဘာစီလိုနာ", "barcelona", "bercelona"],
    "Real Madrid": ["ရီးရဲ", "ရီးရဲလ်", "ရီးရဲမက်ဒရစ်", "real madrid", "realmadrid"],
    "Tottenham Hotspur": ["စပါး", "spur", "hotspur", "tottenham"],
    "Chelsea": ["ချဲလ်ဆီး", "chelsea"],
    "Brighton": ["ဘရိုက်တန်", "brighton"],
    "Newcastle": ["နယူးကာဆယ်", "နယူး", "newcastle", "newcastel"],
    "Sevilla": ["ဆီးဗီလာ", "ဆီးဗီးလား", "sevilla"],
    "Everton": ["အဲဗာတန်", "everton"],
    "Villarreal": ["ဗီလာရီးရဲလ်", "ဗီလာရီရဲ", "villareal", "villarreal"],
}

# =====================================
# FUNCTIONS
# =====================================
def normalize_team(text: str):
    text = text.lower()
    for eng, aliases in TEAM_ALIAS.items():
        for a in aliases:
            if a in text:
                return eng
    return None

def extract_phone(text: str):
    return re.findall(r'(09\d{7,9}|95\d{8,12})', text)

# =====================================
# FILE UPLOAD
# =====================================
uploaded = st.file_uploader("📄 Upload TXT file", type="txt")

if uploaded:
    raw_text = uploaded.read().decode("utf-8", errors="ignore")
    blocks = raw_text.split("\n\n")

    rows = []
    no = 1

    # -----------------------------
    # PARSE DATA
    # -----------------------------
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
                "Teams": teams,                # list (for filter)
                "TeamsText": ", ".join(teams), # string (for display)
                "Phone": ", ".join(phones)
            })
            no += 1

    # -----------------------------
    # TEAM FILTER UI
    # -----------------------------
    all_teams = sorted({t for r in rows for t in r["Teams"]})

    selected_teams = st.multiselect(
        "🔍 ရွေးထားတဲ့ အသင်းတွေကို ခန့်မှန်းထားတဲ့ user တွေကိုပဲ ပြမယ်",
        all_teams
    )

    if selected_teams:
        filtered_rows = [
            r for r in rows
            if any(t in r["Teams"] for t in selected_teams)
        ]
    else:
        filtered_rows = rows

    # -----------------------------
    # DISPLAY TABLE
    # -----------------------------
    st.subheader(f"📊 Result Table (Total: {len(filtered_rows)})")

    display_rows = [
        {
            "No": r["No"],
            "User": r["User"],
            "Teams": r["TeamsText"],
            "Phone": r["Phone"]
        }
        for r in filtered_rows
    ]

    st.dataframe(display_rows, use_container_width=True)

else:
    st.info("⬆️ TXT file ကို အရင် upload လုပ်ပါ")
