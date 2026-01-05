import streamlit as st
import re

st.set_page_config(page_title="Telegram Prediction Analyzer", layout="wide")
st.title("⚽ Telegram Prediction Analyzer")

# ==================================================
# TEAM ALIAS (Myanmar / Typo / Nickname -> English)
# ==================================================
TEAM_ALIAS = {
    "Manchester United": ["မန်ယူ", "man united", "man u", "manutd"],
    "Arsenal": ["အာဆင်နယ်", "arsenal", "aresnal"],
    "Liverpool": ["လီဗာပူး", "liverpool"],
    "Aston Villa": ["ဗီလာ", "အက်စတွန်ဗီလာ", "villa", "aston villa", "astonvilla"],
    "Barcelona": ["ဘာစီ", "ဘာစီလိုနာ", "barcelona"],
    "Chelsea": ["ချဲလ်ဆီး", "chelsea"],
    "Brentford": ["brentford", "ဘရင့်ဖို့ဒ်", "ဘရန့်ဖို့ဒ်"],
    "Fulham": ["fulham", "ဖူလမ်", "ဖူလ်ဟမ်"],
    "Wolves": ["wolves", "wolf", "wolverhampton", "ဝုဗ်", "ဝုလ်ဗ်"],
    "West Ham": ["west ham", "westham", "west ham united", "ဝက်စ်ဟမ်း"],
}

# ==================================================
# UTILITY FUNCTIONS
# ==================================================
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\(.*?\)', ' ', text)          # remove (FT)
    text = re.sub(r'\d+\s*[-:]\s*\d+', ' ', text) # remove scores 2-1
    text = re.sub(r'\bft\b', ' ', text)           # remove ft
    text = re.sub(r'[^\w\s]', ' ', text)          # punctuation / emoji
    text = re.sub(r'\s+', ' ', text).strip()      # normalize spaces
    return text

def normalize_team(text: str):
    cleaned = clean_text(text)
    for eng, aliases in TEAM_ALIAS.items():
        for a in aliases:
            if a in cleaned:
                return eng
    return None

def extract_phone(text: str):
    return re.findall(r'(09\d{7,9}|95\d{8,12})', text)

# ==================================================
# FILE UPLOAD
# ==================================================
uploaded = st.file_uploader("📄 Upload Telegram TXT file", type="txt")

if uploaded:
    raw_text = uploaded.read().decode("utf-8", errors="ignore")

    # split by Telegram message header: "Name, [date]"
    entries = re.split(r'\n(?=[^\n]+,\s*\[\d+/\d+/\d+)', raw_text)

    rows = []
    unknown_teams = set()
    no = 1

    # ==================================================
    # PARSE DATA
    # ==================================================
    for entry in entries:
        lines = [l.strip() for l in entry.splitlines() if l.strip()]
        if len(lines) < 2:
            continue

        user = lines[0].split(",")[0]

        teams = []
        phones = []

        for line in lines[1:]:
            phones_found = extract_phone(line)
            if phones_found:
                phones.extend(phones_found)
            else:
                team = normalize_team(line)
                if team:
                    if team not in teams:
                        teams.append(team)
                else:
                    cleaned = clean_text(line)
                    if cleaned and len(cleaned) > 2:
                        unknown_teams.add(cleaned)

        if teams:
            rows.append({
                "No": no,
                "User": user,
                "Teams": teams,
                "TeamsText": ", ".join(teams),
                "Phone": ", ".join(phones)
            })
            no += 1

    # ==================================================
    # FILTER UI
    # ==================================================
    all_teams = sorted({t for r in rows for t in r["Teams"]})

    selected_teams = st.multiselect(
        "🔍 Select team(s)",
        all_teams
    )

    logic = st.radio(
        "Filter logic",
        ["OR (any selected team)", "AND (all selected teams)"]
    )

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

    # ==================================================
    # DISPLAY MAIN TABLE
    # ==================================================
    st.subheader(f"📊 Result Table (Total: {len(filtered)})")

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

    # ==================================================
    # DISPLAY UNKNOWN TEAMS (CLEANED)
    # ==================================================
    st.subheader("❓ Unknown Teams / Texts (Cleaned)")

    if unknown_teams:
        st.text_area(
            "Not recognized team names:",
            "\n".join(sorted(unknown_teams)),
            height=200
        )
    else:
        st.write("No unknown teams found 🎉")

else:
    st.info("⬆️ TXT file ကို upload လုပ်ပါ")
