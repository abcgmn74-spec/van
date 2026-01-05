import re
import pandas as pd
import streamlit as st

# -----------------------------
# REGEX
# -----------------------------
USER_PATTERN = re.compile(r"^(.*?),\s*\[\d{1,2}/\d{1,2}/\d{4}")
ACCOUNT_PATTERN = re.compile(
    r"((?:ok\s?bet|okbet|okbest|ok\s?bet\.?|okbet_|okbet-?|ok\s?bet-|ok\s?bet/|OKBET|OK\s?BET|\.959|09|၀၉)?"
    r"[0-9၀-၉]{6,})",
    re.IGNORECASE
)

# -----------------------------
# TEAM ALIASES (shortened example)
# -----------------------------
TEAM_ALIASES = {
    "Aston Villa": ["ဗီလာ", "အက်စတွန်ဗီလာ", "aston villa", "villa"],
    "Arsenal": ["အာဆင်နယ်", "arsenal", "arsen"],
    "Barcelona": ["ဘာစီလိုနာ", "ဘာစီ", "barcelona", "barca", "bercelona"],
    "Real Madrid": ["ရီးရဲ", "ရီးရဲလ်မက်ဒရစ်", "real madrid"],
    "Liverpool": ["လီဗာပူး", "လီပါပူး", "liverpool"],
    "Manchester City": ["မန်စီးတီး", "man city", "mancity"],
    "Manchester United": ["မန်ယူ", "man united"],
    "Tottenham Hotspur": ["စပါး", "hotspur", "spur"],
    "Brighton": ["ဘရိုက်တန်", "brighton"],
    "Newcastle": ["နယူးကာဆယ်", "newcastle"],
    "Sevilla": ["ဆီဗီလာ", "sevilla"],
    "Villarreal": ["ဗီလာရီရဲ", "villareal", "villarreal"],
}

def normalize(text):
    return re.sub(r"[^\wက-အ]", "", text.lower())

def resolve_team(text):
    norm = normalize(text)
    for team, aliases in TEAM_ALIASES.items():
        for a in aliases:
            if normalize(a) in norm or norm in normalize(a):
                return team
    return None

def parse_chat(text):
    rows = []
    current_user = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        user_match = USER_PATTERN.search(line)
        if user_match:
            current_user = user_match.group(1)
            continue

        acc_match = ACCOUNT_PATTERN.search(line)
        if acc_match:
            rows.append({"User": current_user, "Team": None, "Account": acc_match.group(1)})
            continue

        team = resolve_team(line)
        if team:
            rows.append({"User": current_user, "Team": team, "Account": None})

    return rows

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("Chat TXT Parser")

uploaded_file = st.file_uploader("Upload chat txt file", type=["txt"])

if uploaded_file:
    text = uploaded_file.read().decode("utf-8")
    data = parse_chat(text)
    df = pd.DataFrame(data)

    st.success("Parsing completed")
    st.dataframe(df)

    st.download_button(
        "Download Excel",
        df.to_excel(index=False),
        file_name="output.xlsx"
    )
