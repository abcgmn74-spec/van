import streamlit as st
import pandas as pd
import re
from thefuzz import process

st.set_page_config(page_title="Football Data Pro Extractor", layout="wide")

# ၁။ Standardized Team Names (Leagues စုံ)
STANDARD_TEAMS = [
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", "Chelsea", 
    "Crystal Palace", "Everton", "Fulham", "Ipswich Town", "Leicester City", 
    "Liverpool", "Manchester City", "Manchester United", "Newcastle United", 
    "Nottingham Forest", "Southampton", "Tottenham Hotspur", "West Ham", "Wolves",
    "Alaves", "Athletic Bilbao", "Atletico Madrid", "Barcelona", "Celta Vigo", 
    "Espanyol", "Getafe", "Girona", "Las Palmas", "Leganes", "Mallorca", 
    "Osasuna", "Real Betis", "Real Madrid", "Real Sociedad", "Sevilla", "Valencia", "Villarreal",
    "AC Milan", "Atalanta", "Bologna", "Cagliari", "Como", "Empoli", "Fiorentina", 
    "Genoa", "Inter Milan", "Juventus", "Lazio", "Monza", "Napoli", "Parma", 
    "AS Roma", "Torino", "Udinese", "Verona"
]

# ၂။ မြန်မာအခေါ်အဝေါ် Variations များကို Standard Name သို့ Mapping လုပ်ခြင်း
TEAM_MAP = {
    # Barcelona (ဘာကာ၊ ဘာဂါ၊ ဘာစီ)
    "ဘာကာ": "Barcelona", "ဘာဂါ": "Barcelona", "ဘာစီ": "Barcelona", "ဘာစီလိုနာ": "Barcelona", "barca": "Barcelona",
    # Real Madrid (Real, ရီးရဲ၊ ရီးရယ်)
    "ရီးရဲ": "Real Madrid", "ရီးရယ်": "Real Madrid", "ရီးရဲလ်": "Real Madrid", "ရီရဲ": "Real Madrid", "real": "Real Madrid", "madrid": "Real Madrid",
    # Manchester United
    "မန်ယူ": "Manchester United", "မန်ယူနိုက်တက်": "Manchester United", "man u": "Manchester United", "manu": "Manchester United",
    # Liverpool
    "လီဗာပူး": "Liverpool", "လီပါပူး": "Liverpool", "လီဗားပူးလ်": "Liverpool", "လီလ်ပါပူး": "Liverpool",
    # Arsenal
    "အာဆင်နယ်": "Arsenal", "အာဆင်နယျ": "Arsenal",
    # Man City
    "မန်စီးတီး": "Manchester City", "မန်စီး": "Manchester City", "mancity": "Manchester City",
    # Other Popular Mappings
    "အဲဗာတန်": "Everton", "စပါး": "Tottenham Hotspur", "နယူး": "Newcastle United", "နယူးကာဆယ်": "Newcastle United",
    "ဘရိုက်တန်": "Brighton", "ဗီလာ": "Aston Villa", "အက်သလက်တီကို": "Atletico Madrid", "ဗယ်လာရီးရဲလ်": "Villarreal",
    "ဆီးဗီလာ": "Sevilla", "ဆီဗီလာ": "Sevilla", "ဂျူဗင်တပ်": "Juventus", "အင်တာ": "Inter Milan", "အေစီမီလန်": "AC Milan"
}

def get_std_team(text):
    text_lower = text.strip().lower()
    # Dictionary ထဲမှာ အရင်စစ်မယ်
    for key, val in TEAM_MAP.items():
        if key.lower() == text_lower or key.lower() in text_lower:
            return val
    # Fuzzy Match (၈၅% ကျော်မှ ယူမည်)
    match, score = process.extractOne(text, STANDARD_TEAMS)
    if score > 85: return match
    return None

st.title("⚽ Football Data Pro Extractor")
st.write("ဘာကာ၊ ဘာဂါ (Barcelona) နှင့် ရီးရဲ၊ ရီးရယ် (Real Madrid) အပါအဝင် အခေါ်အဝေါ်စုံကို ဖတ်ပေးနိုင်ပါသည်။")

uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    
    parsed_data = []
    current_user = None
    user_pattern = re.compile(r'^(.+),\s\[\d{1,2}/\d{1,2}/\d{4}.+\]')

    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = user_pattern.match(line)
        if match:
            if current_user: parsed_data.append(current_user)
            current_user = {"Name": match.group(1), "Phone": "-", "Teams": [], "Other_Comments": []}
            continue
        
        if current_user:
            # ဖုန်းနံပတ် စစ်ခြင်း (ဂဏန်း ၆ လုံးနှင့်အထက်)
            clean_num = re.sub(r'[^0-9]', '', line)
            if len(clean_num) >= 6 and (line.startswith('09') or line.startswith('959') or any(x in line.lower() for x in ['ok', 'bet', 'ph'])):
                current_user["Phone"] = clean_num
            elif len(clean_num) >= 9:
                current_user["Phone"] = clean_num
            else:
                cleaned_text = re.sub(r'^\d+[\s\.\)]+', '', line)
                if cleaned_text and cleaned_text != current_user["Name"]:
                    std_name = get_std_team(cleaned_text)
                    if std_name:
                        if std_name not in current_user["Teams"]:
                            current_user["Teams"].append(std_name)
                    else:
                        current_user["Other_Comments"].append(cleaned_text)

    if current_user: parsed_data.append(current_user)

    # Sidebar Filter
    st.sidebar.header("Filter Settings")
    selected_teams = st.sidebar.multiselect("အသင်းအလိုက် စစ်ထုတ်ရန်:", sorted(STANDARD_TEAMS))

    final_list = []
    for u in parsed_data:
        if selected_teams:
            if not any(t in u['Teams'] for t in selected_teams): continue

        final_list.append({
            "User Name": u['Name'],
            "Phone Number": u['Phone'],
            "Football Teams": ", ".join(u['Teams']),
            "Other Comments": ", ".join(u['Other_Comments'])
        })

    if final_list:
        df = pd.DataFrame(final_list)
        st.success(f"တွေ့ရှိသူစုစုပေါင်း: {len(final_list)} ဦး")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Result သိမ်းရန် (CSV)", csv, "football_report.csv", "text/csv")
    else:
        st.warning("ကိုက်ညီသော အချက်အလက် မတွေ့ပါ။")
